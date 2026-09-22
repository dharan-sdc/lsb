import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import User, AuditLog, Notification

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)

def generate_token(user: User) -> str:
    payload = {
        'user_id': user.id,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'hospital_id': user.hospital_id,
        'blood_group_id': user.blood_group_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')

def decode_token(token: str):
    try:
        return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def jwt_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'message': 'Authorization header missing or invalid format (Bearer token required)'}), 401
            
            token = auth_header.split(' ')[1]
            payload = decode_token(token)
            if not payload:
                return jsonify({'success': False, 'message': 'Token has expired or is invalid. Please login again.'}), 401
            
            g.current_user = payload
            
            if roles:
                user_role = payload.get('role')
                if isinstance(roles, list) and user_role not in roles:
                    return jsonify({'success': False, 'message': f'Access denied. Required roles: {", ".join(roles)}'}), 403
                elif isinstance(roles, str) and user_role != roles:
                    return jsonify({'success': False, 'message': f'Access denied. Required role: {roles}'}), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def log_audit(db, action: str, module: str, details: str = None, user_email: str = None):
    try:
        if not user_email and hasattr(g, 'current_user') and g.current_user:
            user_email = g.current_user.get('email')
        ip_addr = request.remote_addr if request else '127.0.0.1'
        log = AuditLog(
            user_email=user_email,
            action=action,
            module=module,
            details=details,
            ip_address=ip_addr
        )
        db.add(log)
    except Exception as e:
        print(f"Audit log error: {e}")

def create_notification(db, title: str, message: str, notification_type: str = 'info'):
    try:
        notif = Notification(
            title=title,
            message=message,
            type=notification_type,
            is_read=False
        )
        db.add(notif)
    except Exception as e:
        print(f"Notification error: {e}")
