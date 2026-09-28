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
                user_role = str(payload.get('role', '')).lower().replace('_', '').replace(' ', '').replace('-', '')
                allowed_roles = [str(r).lower().replace('_', '').replace(' ', '').replace('-', '') for r in (roles if isinstance(roles, list) else [roles])]
                if user_role not in allowed_roles and 'admin' not in user_role:
                    return jsonify({'success': False, 'message': f'Access denied. Required roles: {", ".join(roles if isinstance(roles, list) else [roles])}'}), 403
            
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

STANDARD_BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

def resolve_blood_group(db, identifier):
    """
    Safely resolves any blood group identifier (DB ID, 1-based index, 0-based index, group name)
    to a valid BloodGroup model instance in the database.
    """
    if identifier is None or identifier == '':
        return None

    from models import BloodGroup

    # 1. Direct database ID lookup
    try:
        int_id = int(identifier)
        bg = db.query(BloodGroup).filter(BloodGroup.id == int_id).first()
        if bg:
            return bg
    except (ValueError, TypeError):
        int_id = None

    # 2. Canonical index lookup (1..8 or 0..7)
    if int_id is not None:
        target_name = None
        if 1 <= int_id <= len(STANDARD_BLOOD_GROUPS):
            target_name = STANDARD_BLOOD_GROUPS[int_id - 1]
        elif 0 <= int_id < len(STANDARD_BLOOD_GROUPS):
            target_name = STANDARD_BLOOD_GROUPS[int_id]

        if target_name:
            bg = db.query(BloodGroup).filter(BloodGroup.group_name.ilike(target_name)).first()
            if bg:
                return bg

    # 3. String name lookup (exact or partial)
    if isinstance(identifier, str):
        clean_str = identifier.strip().upper()
        bg = db.query(BloodGroup).filter(BloodGroup.group_name.ilike(clean_str)).first()
        if bg:
            return bg
        for std in STANDARD_BLOOD_GROUPS:
            if std.upper() == clean_str or std.upper() in clean_str or clean_str in std.upper():
                bg = db.query(BloodGroup).filter(BloodGroup.group_name.ilike(std)).first()
                if bg:
                    return bg

    return None

