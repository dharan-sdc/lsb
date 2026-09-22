from datetime import datetime, timezone
from database import get_db
from models import User
from auth_utils import hash_password, verify_password, generate_token, log_audit

class AuthController:
    @staticmethod
    def login(email, password):
        email = (email or '').strip().lower()
        if not email or not password:
            return {'success': False, 'message': 'Email/Username and Password are required'}, 400

        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return {'success': False, 'message': 'Invalid credentials. User not found.'}, 401

            if user.status != 'Active':
                return {'success': False, 'message': f'Account is {user.status.lower()}. Please contact administrator.'}, 403

            if not verify_password(password, user.password_hash):
                return {'success': False, 'message': 'Invalid credentials. Incorrect password.'}, 401

            user.last_login = datetime.now(timezone.utc)
            token = generate_token(user)
            log_audit(db, 'LOGIN_SUCCESS', 'Auth', f'User {user.email} logged in successfully', user_email=user.email)
            db.commit()

            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }, 200

    @staticmethod
    def register(name, email, password, role='User', phone='', blood_group_id=None, age=None, gender=None, address=None, hospital_id=None):
        name = (name or '').strip()
        email = (email or '').strip().lower()

        if not name or not email or not password:
            return {'success': False, 'message': 'Name, Email and Password are required'}, 400

        if len(password) < 6:
            return {'success': False, 'message': 'Password must be at least 6 characters'}, 400

        valid_roles = ['User', 'Hospital', 'BloodBank', 'Admin']
        assigned_role = role if role in valid_roles else 'User'

        with get_db() as db:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return {'success': False, 'message': 'Email is already registered'}, 409

            try:
                blood_group_id = int(blood_group_id) if blood_group_id else None
            except (ValueError, TypeError):
                blood_group_id = None

            try:
                age = int(age) if age else None
            except (ValueError, TypeError):
                age = None

            try:
                hospital_id = int(hospital_id) if hospital_id else None
            except (ValueError, TypeError):
                hospital_id = None

            new_user = User(
                name=name,
                email=email,
                password_hash=hash_password(password),
                role=assigned_role,
                status='Active',
                phone=phone,
                blood_group_id=blood_group_id,
                age=age,
                gender=gender,
                address=address,
                hospital_id=hospital_id
            )
            db.add(new_user)
            db.flush()
            
            token = generate_token(new_user)
            log_audit(db, 'USER_REGISTERED', 'Auth', f'New user {new_user.email} registered with role {assigned_role}', user_email=new_user.email)
            db.commit()

            return {
                'success': True,
                'message': 'Registration successful',
                'token': token,
                'user': new_user.to_dict()
            }, 201

    @staticmethod
    def forgot_password(email):
        email = (email or '').strip().lower()
        if not email:
            return {'success': False, 'message': 'Email is required'}, 400

        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return {'success': False, 'message': 'No account found with this email address.'}, 404

            demo_otp = "123456"
            log_audit(db, 'PASSWORD_RESET_REQUESTED', 'Auth', f'Password reset OTP sent to {email}', user_email=email)
            db.commit()

            return {
                'success': True,
                'message': 'Password reset OTP has been sent to your email (Demo OTP: 123456)',
                'demo_otp': demo_otp,
                'email': email
            }, 200

    @staticmethod
    def reset_password(email, otp, new_password):
        email = (email or '').strip().lower()
        otp = (otp or '').strip()

        if not email or not otp or not new_password:
            return {'success': False, 'message': 'Email, OTP, and New Password are required'}, 400

        if otp != "123456" and len(otp) != 6:
            return {'success': False, 'message': 'Invalid OTP code. Please enter the 6-digit OTP.'}, 400

        if len(new_password) < 6:
            return {'success': False, 'message': 'New password must be at least 6 characters'}, 400

        with get_db() as db:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            user.password_hash = hash_password(new_password)
            log_audit(db, 'PASSWORD_RESET_COMPLETED', 'Auth', f'Password reset successfully for {email}', user_email=email)
            db.commit()

            return {
                'success': True,
                'message': 'Password has been reset successfully. You can now login with your new password.'
            }, 200

    @staticmethod
    def get_current_user(user_id):
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404
            return {'success': True, 'user': user.to_dict()}, 200

    @staticmethod
    def update_profile(user_id, data):
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            if 'name' in data and data['name']:
                user.name = data['name'].strip()
            if 'phone' in data:
                user.phone = data['phone']
            if 'age' in data and data['age']:
                try:
                    user.age = int(data['age'])
                except ValueError:
                    pass
            if 'gender' in data:
                user.gender = data['gender']
            if 'blood_group_id' in data and data['blood_group_id']:
                try:
                    user.blood_group_id = int(data['blood_group_id'])
                except ValueError:
                    pass
            if 'address' in data:
                user.address = data['address']

            log_audit(db, 'PROFILE_UPDATED', 'Auth', f'User {user.email} updated profile', user_email=user.email)
            db.commit()
            return {'success': True, 'message': 'Profile updated successfully', 'user': user.to_dict()}, 200
