from database import get_db
from models import User
from auth_utils import hash_password, log_audit

class AdminController:
    @staticmethod
    def list_users(search='', role_filter='', status_filter=''):
        with get_db() as db:
            query = db.query(User)
            if search:
                query = query.filter((User.name.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%')))
            if role_filter:
                query = query.filter(User.role == role_filter)
            if status_filter:
                query = query.filter(User.status == status_filter)

            users = query.order_by(User.id.asc()).all()
            return {
                'success': True,
                'count': len(users),
                'users': [u.to_dict() for u in users]
            }, 200

    @staticmethod
    def create_user(name, email, password, role='Staff', status='Active', phone=''):
        name = (name or '').strip()
        email = (email or '').strip().lower()

        if not name or not email or not password:
            return {'success': False, 'message': 'Name, email, and password are required'}, 400

        if len(password) < 6:
            return {'success': False, 'message': 'Password must be at least 6 characters'}, 400

        with get_db() as db:
            if db.query(User).filter(User.email == email).first():
                return {'success': False, 'message': 'User with this email already exists'}, 409

            user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=role if role in ['Admin', 'Staff', 'Doctor'] else 'Staff',
                status=status,
                phone=phone
            )
            db.add(user)
            db.flush()
            log_audit(db, 'USER_CREATED', 'Admin', f'Created user {email} with role {role}')
            db.commit()

            return {
                'success': True,
                'message': 'User created successfully',
                'user': user.to_dict()
            }, 201

    @staticmethod
    def update_user(user_id, data):
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            if 'name' in data and data['name']:
                user.name = data['name'].strip()
            if 'role' in data and data['role']:
                user.role = data['role']
            if 'status' in data and data['status']:
                user.status = data['status']
            if 'phone' in data:
                user.phone = data['phone']
            if 'password' in data and data['password']:
                if len(data['password']) < 6:
                    return {'success': False, 'message': 'Password must be at least 6 characters'}, 400
                user.password_hash = hash_password(data['password'])

            log_audit(db, 'USER_UPDATED', 'Admin', f'Updated user id {user_id} ({user.email})')
            db.commit()

            return {
                'success': True,
                'message': 'User updated successfully',
                'user': user.to_dict()
            }, 200

    @staticmethod
    def delete_user(user_id, current_user_id):
        if user_id == current_user_id:
            return {'success': False, 'message': 'Cannot delete your own logged-in account'}, 400

        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            if user.email == 'admin@bloodbank.com':
                return {'success': False, 'message': 'Primary system administrator account cannot be deleted'}, 403

            deleted_email = user.email
            db.delete(user)
            log_audit(db, 'USER_DELETED', 'Admin', f'Deleted user {deleted_email}')
            db.commit()

            return {'success': True, 'message': f'User {deleted_email} deleted successfully'}, 200

    @staticmethod
    def manage_role(user_id, new_role):
        if not new_role or new_role not in ['Admin', 'Staff', 'Doctor']:
            return {'success': False, 'message': 'Invalid role. Choose Admin, Staff, or Doctor'}, 400

        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            user.role = new_role
            log_audit(db, 'ROLE_CHANGED', 'Admin', f'Changed role of {user.email} to {new_role}')
            db.commit()

            return {'success': True, 'message': f'Role updated to {new_role}', 'user': user.to_dict()}, 200
