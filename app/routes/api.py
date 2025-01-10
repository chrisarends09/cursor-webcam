from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models.webcam import Webcam, UserWebcam
from datetime import datetime, timedelta
from app.models.user import User
from app.utils.email import send_password_reset_email
from app.utils.auth import require_api_token, generate_api_token
import psutil
import os
from app.utils.rate_limit import rate_limit
from app.utils.monitoring import monitor_errors

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/webcams', methods=['GET'])
@login_required
@rate_limit(limit=100, window=60)  # 100 requests per minute
@monitor_errors
def get_webcams():
    """Get all webcams available to the user"""
    webcams = Webcam.query.all()
    return jsonify([{
        'id': w.id,
        'name': w.name,
        'description': w.description,
        'url': w.url,
        'type': w.type,
        'resort': w.resort
    } for w in webcams])

@api_bp.route('/webcams/user', methods=['GET'])
@login_required
def get_user_webcams():
    """Get webcams configured for the current user"""
    user_webcams = UserWebcam.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': uw.webcam.id,
        'name': uw.webcam.name,
        'interval_hours': uw.interval_hours,
        'last_capture': uw.last_capture.isoformat() if uw.last_capture else None,
        'next_capture': uw.next_capture.isoformat() if uw.next_capture else None
    } for uw in user_webcams])

@api_bp.route('/webcams/<int:webcam_id>/capture', methods=['POST'])
@login_required
def capture_webcam(webcam_id):
    """Trigger a webcam capture"""
    from app.utils.webcam_capture import capture_webcam
    
    user_webcam = UserWebcam.query.filter_by(
        user_id=current_user.id,
        webcam_id=webcam_id
    ).first_or_404()
    
    success = capture_webcam(user_webcam.webcam)
    if success:
        user_webcam.last_capture = datetime.utcnow()
        if user_webcam.interval_hours:
            user_webcam.next_capture = datetime.utcnow() + timedelta(hours=user_webcam.interval_hours)
        db.session.commit()
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Failed to capture webcam'}), 500 

@api_bp.route('/user/profile', methods=['GET'])
@login_required
def get_profile():
    """Get current user's profile"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'created_at': current_user.created_at.isoformat(),
        'webcam_count': current_user.webcams.count()
    })

@api_bp.route('/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    if 'email' in data:
        # Check if email is already taken
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'status': 'error', 'message': 'Email already taken'}), 400
        current_user.email = data['email']
    
    if 'password' in data:
        current_user.set_password(data['password'])
    
    db.session.commit()
    return jsonify({'status': 'success'})

@api_bp.route('/user/webcams/stats', methods=['GET'])
@login_required
def get_webcam_stats():
    """Get user's webcam statistics"""
    user_webcams = UserWebcam.query.filter_by(user_id=current_user.id).all()
    
    stats = {
        'total_webcams': len(user_webcams),
        'active_schedules': sum(1 for uw in user_webcams if uw.interval_hours is not None),
        'captures_today': sum(1 for uw in user_webcams if uw.last_capture and 
                            uw.last_capture.date() == datetime.utcnow().date()),
        'next_captures': [
            {
                'webcam_name': uw.webcam.name,
                'next_capture': uw.next_capture.isoformat() if uw.next_capture else None
            }
            for uw in user_webcams if uw.next_capture
        ]
    }
    
    return jsonify(stats) 

@api_bp.route('/auth/token', methods=['POST'])
@login_required
def get_api_token():
    """Get an API token for the current user"""
    token = generate_api_token(current_user)
    return jsonify({
        'token': token,
        'expires_in': 30 * 24 * 60 * 60  # 30 days in seconds
    })

@api_bp.route('/system/status', methods=['GET'])
@require_api_token
@rate_limit(limit=60, window=60)  # 60 requests per minute
@monitor_errors
def get_system_status():
    """Get system status information"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get snapshot storage info
    snapshots_dir = os.path.join(current_app.root_path, '..', 'snapshots')
    total_snapshots = 0
    total_size = 0
    if os.path.exists(snapshots_dir):
        for dirpath, dirnames, filenames in os.walk(snapshots_dir):
            total_snapshots += len(filenames)
            total_size += sum(os.path.getsize(os.path.join(dirpath, f)) for f in filenames)
    
    return jsonify({
        'system': {
            'cpu_percent': cpu_percent,
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'free': disk.free,
                'percent': disk.percent
            }
        },
        'application': {
            'snapshots': {
                'count': total_snapshots,
                'size': total_size
            },
            'users': {
                'total': User.query.count(),
                'active': User.query.filter(User.last_login > datetime.utcnow() - timedelta(days=7)).count()
            },
            'webcams': {
                'total': Webcam.query.count(),
                'active': UserWebcam.query.filter(UserWebcam.interval_hours.isnot(None)).count()
            }
        }
    })

@api_bp.route('/system/snapshots', methods=['GET'])
@require_api_token
@rate_limit(limit=30, window=60)  # 30 requests per minute
def get_snapshot_stats():
    """Get detailed snapshot statistics"""
    snapshots_dir = os.path.join(current_app.root_path, '..', 'snapshots')
    stats = {
        'by_webcam': {},
        'by_date': {},
        'total_size': 0,
        'total_count': 0
    }
    
    if os.path.exists(snapshots_dir):
        for dirpath, dirnames, filenames in os.walk(snapshots_dir):
            for filename in filenames:
                if filename.endswith(('.jpg', '.png')):
                    filepath = os.path.join(dirpath, filename)
                    size = os.path.getsize(filepath)
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    date_key = mtime.strftime('%Y-%m-%d')
                    
                    # Extract webcam name from filename
                    webcam_name = filename.split('_')[0]
                    
                    # Update webcam stats
                    if webcam_name not in stats['by_webcam']:
                        stats['by_webcam'][webcam_name] = {'count': 0, 'size': 0}
                    stats['by_webcam'][webcam_name]['count'] += 1
                    stats['by_webcam'][webcam_name]['size'] += size
                    
                    # Update date stats
                    if date_key not in stats['by_date']:
                        stats['by_date'][date_key] = {'count': 0, 'size': 0}
                    stats['by_date'][date_key]['count'] += 1
                    stats['by_date'][date_key]['size'] += size
                    
                    stats['total_size'] += size
                    stats['total_count'] += 1
    
    return jsonify(stats) 