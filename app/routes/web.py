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


@web_bp.before_request
def require_login():
    # Allow landing page and authentication endpoints
    allowed_endpoints = ['web.login', 'web.register', 'web.index', 'static']
    if request.endpoint in allowed_endpoints:
        return

    if not session.get('user_id'):
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('web.login'))

    logged_in_user_id = session.get('user_id')
    logged_in_username = session.get('username')
    requested_user_id = request.view_args.get('user_id') if request.view_args else None

    if logged_in_username == 'admins':
        if request.endpoint == 'web.user_portal':
            flash('Admin tidak dapat masuk ke portal pengguna.', 'info')
            return redirect(url_for('web.admin_dashboard'))
    else:
        if request.endpoint == 'web.admin_dashboard':
            flash('Anda tidak memiliki akses ke halaman admin.', 'error')
            return redirect(url_for('web.user_portal', user_id=logged_in_user_id))

        if requested_user_id and requested_user_id != logged_in_user_id:
            if request.endpoint not in ['web.verify', 'web.result']:
                flash('Anda tidak memiliki akses ke halaman tersebut.', 'error')
                return redirect(url_for('web.user_portal', user_id=logged_in_user_id))


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User and Admin Login"""
    selected_role = request.form.get('role') or request.args.get('role')

    if session.get('user_id'):
        if session.get('username') == 'admins':
            return redirect(url_for('web.admin_dashboard'))
        return redirect(url_for('web.user_portal', user_id=session.get('user_id')))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        selected_role = request.form.get('role') or request.args.get('role')

        if not username or not password:
            flash('Username dan password harus diisi', 'error')
            return render_template('login.html', selected_role=selected_role)

        user = db.session.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Selamat datang kembali, {user.full_name or user.username}!', 'success')

            if user.username == 'admins':
                return redirect(url_for('web.admin_dashboard'))
            return redirect(url_for('web.user_portal', user_id=user.id))

        flash('Username atau password salah', 'error')

    return render_template('login.html', selected_role=selected_role)


@web_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Anda telah berhasil logout.', 'success')
    return redirect(url_for('web.index'))


@web_bp.route('/user/<int:user_id>')
def user_portal(user_id):
    """User portal - upload signatures and verify."""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            flash('User tidak ditemukan', 'error')
            return redirect(url_for('web.register'))

        sig_count = user.reference_signatures.count()
        reference_signatures = user.reference_signatures.all()
        
        # Get history where the user is either the target or the verifier
        history_list = db.session.query(VerificationHistory).filter(
            (VerificationHistory.user_id == user_id) | (VerificationHistory.verified_by_user_id == user_id)
        ).order_by(
            VerificationHistory.verification_date.desc()
        ).limit(10).all()

        # Get all registered users (excluding admin) for the target verification dropdown
        registered_users = db.session.query(User).filter(
            User.is_registered == True,
            User.username != 'admins'
        ).all()

        return render_template(
            'user/dashboard.html',
            user=user,
            sig_count=sig_count,
            reference_signatures=reference_signatures,
            history_list=history_list,
            registered_users=registered_users
        )
    except Exception as e:
        logger.error(f"Error in user_portal: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.index'))



@web_bp.route('/')
def index():
    """Landing page for unauthenticated users."""
    if session.get('user_id'):
        if session.get('username') == 'admins':
            return redirect(url_for('web.admin_dashboard'))
        return redirect(url_for('web.user_portal', user_id=session.get('user_id')))
    return render_template('landing.html')


@web_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard for monitoring signature verification history."""
    if session.get('username') != 'admins':
        if session.get('user_id'):
            return redirect(url_for('web.user_portal', user_id=session['user_id']))
        return redirect(url_for('web.login'))

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
        
        users_list = db.session.query(User).filter(User.username != 'admins').all()
        
        # Calculate system accuracy (average confidence)
        avg_confidence = db.session.query(
            db.func.avg(VerificationHistory.confidence)
        ).scalar() or 0.0
        
        stats = {
            'total_users': total_users,
            'registered_users': registered_users,
            'total_verifications': total_verifications,
            'genuine_count': genuine_count,
            'forged_count': forged_count,
            'recent_verifications': recent_verifications,
            'users_list': users_list,
            'avg_confidence': float(avg_confidence)
        }
        
        return render_template('admin/dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Error in admin_dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return render_template('admin/dashboard.html', stats={})


@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register signatures"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            full_name = request.form.get('full_name', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not username or not email or not password:
                flash('Username, email, and password are required', 'error')
                return redirect(url_for('web.register'))
                
            if password != confirm_password:
                flash('Passwords do not match', 'error')
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
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # If not logged in as admin, log in as the newly created user
            if session.get('username') != 'admins':
                session['user_id'] = user.id
                session['username'] = user.username
                flash(f'User {username} created! Now upload your signatures.', 'success')
            else:
                flash(f'User {username} created successfully! You can now upload signatures for them.', 'success')
                
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
                return redirect(url_for('web.user_portal', user_id=user_id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error registering signatures: {str(e)}")
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('web.user_portal', user_id=user_id))
        
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
                
                # Get verified_by_user_id (current logged in user) and description
                verified_by_user_id = session.get('user_id')
                description = request.form.get('description', '').strip()
                
                # Run verification
                predictor = get_predictor(current_app.config)
                result = predictor.verify_user_signature(
                    user_id,
                    test_image_path,
                    db.session,
                    current_app.config,
                    verified_by_user_id=verified_by_user_id,
                    description=description
                )
                
                new_history = db.session.query(VerificationHistory).filter_by(user_id=user_id).order_by(
                    VerificationHistory.verification_date.desc()
                ).first()
                
                return redirect(url_for('web.result', user_id=user_id, history_id=new_history.id))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during verification: {str(e)}")
                flash(f'Error: {str(e)}', 'error')
                return redirect(url_for('web.user_portal', user_id=session.get('user_id')))
        
        # Verification form is embedded in user dashboard — redirect there
        return redirect(url_for('web.user_portal', user_id=user_id))
        
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
        verifications = db.session.query(VerificationHistory).filter(
            (VerificationHistory.user_id == user_id) | (VerificationHistory.verified_by_user_id == user_id)
        ).order_by(
            VerificationHistory.verification_date.desc()
        ).paginate(page=page, per_page=10)
        
        return render_template('history.html', user=user, verifications=verifications)
        
    except Exception as e:
        logger.error(f"Error in history: {str(e)}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('web.index'))
