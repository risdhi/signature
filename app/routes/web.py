from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask import current_app
import os
from pathlib import Path
import logging

from app.extensions import db
from app.database.models import User, ReferenceSignature, VerificationHistory
from app.ai.predictor import get_predictor
from app.utils.image_utils import save_uploaded_file, allowed_file

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)


@web_bp.route('/user/<int:user_id>')
def user_portal(user_id):
    """User portal - upload & verify in one page"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('User tidak ditemukan', 'error')
            return redirect(url_for('web.register'))

        sig_count = user.reference_signatures.count()
        histories = user.verification_history.order_by(
            VerificationHistory.verification_date.desc()
        ).limit(10).all()

        return render_template('user_portal.html', user=user, sig_count=sig_count, histories=histories)
    except Exception as e:
        logger.error(f"Error in user_portal: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.index'))



@web_bp.route('/')
def index():
    """Dashboard"""
    try:
        total_users = db.session.query(User).count()
        registered_users = db.session.query(User).filter_by(is_registered=True).count()
        total_verifications = db.session.query(VerificationHistory).count()
        recent_verifications = db.session.query(VerificationHistory).order_by(
            VerificationHistory.verification_date.desc()
        ).limit(5).all()
        
        genuine_count = db.session.query(VerificationHistory).filter_by(
            prediction='GENUINE'
        ).count()
        forged_count = db.session.query(VerificationHistory).filter_by(
            prediction='FORGED'
        ).count()
        
        stats = {
            'total_users': total_users,
            'registered_users': registered_users,
            'total_verifications': total_verifications,
            'genuine_count': genuine_count,
            'forged_count': forged_count,
            'recent_verifications': recent_verifications[:5]
        }
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        logger.error(f"Error in index: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('index.html', stats={})


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register signatures"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            
            if not username or not email:
                flash('Username and email are required', 'error')
                return redirect(url_for('web.register'))
            
            # Check if user exists
            existing_user = db.session.query(User).filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return redirect(url_for('web.register'))
            
            # Create user
            user = User(
                username=username,
                email=email,
                full_name=full_name
            )
            db.session.add(user)
            db.session.commit()
            
            session['user_id'] = user.id
            session['username'] = user.username
            
            flash(f'User {username} created! Now upload your signatures.', 'success')
            return redirect(url_for('web.upload_signatures', user_id=user.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {str(e)}")
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('register.html')


@web_bp.route('/upload-signatures/<int:user_id>', methods=['GET', 'POST'])
def upload_signatures(user_id):
    """Upload reference signatures"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('web.register'))
        
        if request.method == 'POST':
            # Check if files uploaded
            if 'files' not in request.files:
                flash('No files selected', 'error')
                return redirect(request.url)
            
            files = request.files.getlist('files')
            
            if len(files) == 0:
                flash('No files selected', 'error')
                return redirect(request.url)
            
            if len(files) < current_app.config['MIN_REFERENCE_SIGNATURES']:
                flash(f"Upload at least {current_app.config['MIN_REFERENCE_SIGNATURES']} signatures", 'error')
                return redirect(request.url)
            
            if len(files) > current_app.config['MAX_REFERENCE_SIGNATURES']:
                flash(f"Upload maximum {current_app.config['MAX_REFERENCE_SIGNATURES']} signatures", 'error')
                return redirect(request.url)
            
            # Save and process files
            try:
                predictor = get_predictor(current_app.config)
                
                image_paths = []
                for file in files:
                    if file and allowed_file(file.filename):
                        filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                        image_paths.append(filepath)
                
                if len(image_paths) < len(files):
                    flash('Some files were invalid and skipped', 'warning')
                
                # Register signatures
                predictor.register_signatures(
                    user_id,
                    image_paths,
                    db.session,
                    current_app.config['UPLOAD_FOLDER']
                )
                
                # Update user status
                user.is_registered = True
                db.session.commit()
                
                session['user_id'] = user_id
                session['username'] = user.username
                
                flash(f'Successfully registered {len(image_paths)} signatures!', 'success')
                return redirect(url_for('web.verify', user_id=user_id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error registering signatures: {str(e)}")
                flash(f'Error: {str(e)}', 'error')
                return redirect(request.url)
        
        return render_template('register.html', user=user, upload_page=True)
        
    except Exception as e:
        logger.error(f"Error in upload_signatures: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.register'))


@web_bp.route('/verify/<int:user_id>', methods=['GET', 'POST'])
def verify(user_id):
    """Verify signature"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('web.register'))
        
        if not user.is_registered:
            flash('User not registered yet. Please register signatures first.', 'warning')
            return redirect(url_for('web.upload_signatures', user_id=user_id))
        
        if request.method == 'POST':
            try:
                if 'file' not in request.files:
                    flash('No file selected', 'error')
                    return redirect(request.url)
                
                file = request.files['file']
                if not file or not allowed_file(file.filename):
                    flash('Invalid file', 'error')
                    return redirect(request.url)
                
                # Save test image
                test_image_path = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                
                # Run verification
                predictor = get_predictor(current_app.config)
                result = predictor.verify_user_signature(
                    user_id,
                    test_image_path,
                    db.session,
                    current_app.config
                )
                
                session['user_id'] = user_id
                session['username'] = user.username
                
                return redirect(url_for('web.result', user_id=user_id, history_id=
                    db.session.query(VerificationHistory).filter_by(user_id=user_id).order_by(
                        VerificationHistory.verification_date.desc()
                    ).first().id
                ))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during verification: {str(e)}")
                flash(f'Error: {str(e)}', 'error')
                return redirect(request.url)
        
        reference_count = user.reference_signatures.count()
        return render_template('verify.html', user=user, reference_count=reference_count)
        
    except Exception as e:
        logger.error(f"Error in verify: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.register'))


@web_bp.route('/result/<int:user_id>/<int:history_id>')
def result(user_id, history_id):
    """Show verification result"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        history = db.session.query(VerificationHistory).filter_by(id=history_id).first()
        
        if not user or not history:
            flash('Result not found', 'error')
            return redirect(url_for('web.index'))
        
        session['user_id'] = user_id
        session['username'] = user.username
        
        return render_template('result.html', user=user, history=history)
        
    except Exception as e:
        logger.error(f"Error in result: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.index'))


@web_bp.route('/history/<int:user_id>')
def history(user_id):
    """View verification history"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('web.register'))
        
        page = request.args.get('page', 1, type=int)
        verifications = user.verification_history.order_by(
            VerificationHistory.verification_date.desc()
        ).paginate(page=page, per_page=10)
        
        session['user_id'] = user_id
        session['username'] = user.username
        
        return render_template('history.html', user=user, verifications=verifications)
        
    except Exception as e:
        logger.error(f"Error in history: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.index'))
