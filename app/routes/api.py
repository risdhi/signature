from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

from app.extensions import db
from app.database.models import User, ReferenceSignature, VerificationHistory
from app.ai.predictor import get_predictor
from app.utils.image_utils import save_uploaded_file, allowed_file
from app.utils.helpers import format_response, error_response, require_data

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check"""
    return format_response(message='API is healthy', data={'status': 'online'})


@api_bp.route('/users', methods=['GET'])
def get_users():
    """Get all users"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        users = db.session.query(User).paginate(page=page, per_page=per_page)
        
        data = {
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'users': [user.to_dict() for user in users.items]
        }
        
        return format_response(data=data)
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user details"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return error_response('User not found', status_code=404)
        
        data = user.to_dict()
        data['reference_signatures'] = [sig.to_dict() for sig in user.reference_signatures]
        
        return format_response(data=data)
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users', methods=['POST'])
@require_data('username', 'email')
def create_user():
    """Create new user"""
    try:
        data = request.json
        
        # Check if user exists
        existing = db.session.query(User).filter_by(username=data['username']).first()
        if existing:
            return error_response('Username already exists', status_code=409)
        
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', '')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return format_response(
            message='User created successfully',
            data=user.to_dict(),
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating user: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users/<int:user_id>/register', methods=['POST'])
def register_signatures(user_id):
    """Register reference signatures"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return error_response('User not found', status_code=404)
        
        # Check if files uploaded
        if 'files' not in request.files:
            return error_response('No files uploaded', status_code=400)
        
        files = request.files.getlist('files')
        
        if len(files) < current_app.config['MIN_REFERENCE_SIGNATURES']:
            return error_response(
                f"Upload at least {current_app.config['MIN_REFERENCE_SIGNATURES']} signatures",
                status_code=400
            )
        
        # Save and process files
        image_paths = []
        for file in files:
            if file and allowed_file(file.filename):
                filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                image_paths.append(filepath)
        
        if len(image_paths) == 0:
            return error_response('No valid files found', status_code=400)
        
        # Register signatures
        predictor = get_predictor(current_app.config)
        ref_sigs = predictor.register_signatures(
            user_id,
            image_paths,
            db.session,
            current_app.config['UPLOAD_FOLDER']
        )
        
        # Update user status
        user.is_registered = True
        db.session.commit()
        
        return format_response(
            message=f'Registered {len(ref_sigs)} signatures',
            data={
                'user_id': user_id,
                'signatures_count': len(ref_sigs),
                'is_registered': True
            }
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error registering signatures: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users/<int:user_id>/verify', methods=['POST'])
def verify_signature(user_id):
    """Verify signature"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return error_response('User not found', status_code=404)
        
        if not user.is_registered:
            return error_response('User not registered', status_code=400)
        
        # Check if file uploaded
        if 'file' not in request.files:
            return error_response('No file uploaded', status_code=400)
        
        file = request.files['file']
        if not file or not allowed_file(file.filename):
            return error_response('Invalid file', status_code=400)
        
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
        
        return format_response(
            message='Verification completed',
            data=result
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error verifying signature: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users/<int:user_id>/verification-history', methods=['GET'])
def get_verification_history(user_id):
    """Get verification history for user"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return error_response('User not found', status_code=404)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        verifications = user.verification_history.order_by(
            VerificationHistory.verification_date.desc()
        ).paginate(page=page, per_page=per_page)
        
        data = {
            'total': verifications.total,
            'pages': verifications.pages,
            'current_page': page,
            'verifications': [v.to_dict() for v in verifications.items]
        }
        
        return format_response(data=data)
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/users/<int:user_id>/reference-signatures', methods=['GET'])
def get_reference_signatures(user_id):
    """Get reference signatures for user"""
    try:
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return error_response('User not found', status_code=404)
        
        signatures = [sig.to_dict() for sig in user.reference_signatures]
        
        return format_response(data={
            'user_id': user_id,
            'count': len(signatures),
            'signatures': signatures
        })
    except Exception as e:
        logger.error(f"Error getting signatures: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/verification/<int:history_id>', methods=['GET'])
def get_verification_result(history_id):
    """Get verification result"""
    try:
        history = db.session.query(VerificationHistory).filter_by(id=history_id).first()
        if not history:
            return error_response('Verification not found', status_code=404)
        
        return format_response(data=history.to_dict())
    except Exception as e:
        logger.error(f"Error getting verification: {str(e)}")
        return error_response(str(e), status_code=500)


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        total_users = db.session.query(User).count()
        registered_users = db.session.query(User).filter_by(is_registered=True).count()
        total_verifications = db.session.query(VerificationHistory).count()
        
        genuine_count = db.session.query(VerificationHistory).filter_by(
            prediction='GENUINE'
        ).count()
        forged_count = db.session.query(VerificationHistory).filter_by(
            prediction='FORGED'
        ).count()
        
        avg_confidence = db.session.query(
            db.func.avg(VerificationHistory.confidence)
        ).scalar() or 0
        
        stats = {
            'total_users': total_users,
            'registered_users': registered_users,
            'total_verifications': total_verifications,
            'genuine_predictions': genuine_count,
            'forged_predictions': forged_count,
            'average_confidence': float(avg_confidence),
            'accuracy': (genuine_count + forged_count) / max(total_verifications, 1) * 100 if total_verifications > 0 else 0
        }
        
        return format_response(data=stats)
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return error_response(str(e), status_code=500)
