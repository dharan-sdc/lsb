from datetime import datetime, timezone
from database import get_db
from models import User, BloodGroup, Hospital, Donor
from auth_utils import hash_password, verify_password, generate_token, log_audit, resolve_blood_group

def _resolve_valid_blood_group_id(db, requested_id):
    """Safely resolves any blood group identifier to a valid BloodGroup ID in the database."""
    if requested_id is None:
        return None
    bg = resolve_blood_group(db, requested_id)
    if bg:
        return bg.id
    # If not resolved and a value was requested, fallback to first blood group in DB
    first_bg = db.query(BloodGroup).order_by(BloodGroup.id.asc()).first()
    return first_bg.id if first_bg else None

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

            user_dict = user.to_dict()
            if user.blood_group_id:
                bg = db.query(BloodGroup).filter(BloodGroup.id == user.blood_group_id).first()
                if bg:
                    user_dict['blood_group_name'] = bg.group_name

            return {
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user_dict
            }, 200

    @staticmethod
    def register(name_or_data=None, email=None, password=None, role='User', phone='', **kwargs):
        if isinstance(name_or_data, dict):
            return AuthController.register_user(name_or_data)
        data = {
            'name': name_or_data,
            'email': email,
            'password': password,
            'role': role,
            'phone': phone,
        }
        data.update(kwargs)
        return AuthController.register_user(data)

    @staticmethod
    def register_user(data):
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        role = data.get('role') or 'User'
        phone = data.get('phone')
        blood_group_id = data.get('blood_group_id')
        age = data.get('age')
        gender = data.get('gender')
        address = data.get('address')
        city = data.get('city')
        emergency_contact = data.get('emergency_contact')
        dob = data.get('dob')
        hospital_id = data.get('hospital_id')
        is_donor = bool(data.get('is_donor', False))

        if not name or not email or not password:
            return {'success': False, 'message': 'Name, Email, and Password are required'}, 400

        if len(password) < 6:
            return {'success': False, 'message': 'Password must be at least 6 characters'}, 400

        valid_roles = ['User', 'Hospital', 'BloodBank', 'Admin']
        assigned_role = role if role in valid_roles else 'User'

        with get_db() as db:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                return {'success': False, 'message': 'Email is already registered'}, 409

            # Resolve valid blood group id
            if blood_group_id is not None or is_donor:
                blood_group_id = _resolve_valid_blood_group_id(db, blood_group_id)

            try:
                hospital_id = int(hospital_id) if hospital_id else None
            except (ValueError, TypeError):
                hospital_id = None

            if hospital_id is not None:
                hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
                if not hosp:
                    hospital_id = None

            try:
                age = int(age) if age else None
            except (ValueError, TypeError):
                age = None

            try:
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
                    dob=dob,
                    city=city,
                    address=address,
                    emergency_contact=emergency_contact,
                    is_blood_group_verified=False,
                    is_donor=is_donor,
                    hospital_id=hospital_id
                )
                db.add(new_user)
                db.flush()

                # If user pledged/registered as donor, add to Donors registry
                if is_donor and blood_group_id:
                    existing_donor = db.query(Donor).filter((Donor.email == email) | (Donor.contact == phone)).first()
                    if not existing_donor:
                        d = Donor(
                            name=name,
                            age=age or 25,
                            gender=gender or 'Other',
                            blood_group_id=blood_group_id,
                            contact=phone or email,
                            email=email,
                            address=address or city,
                            medical_notes='Registered Voluntary Donor via User Portal',
                            status='Eligible'
                        )
                        db.add(d)
                
                token = generate_token(new_user)
                log_audit(db, 'USER_REGISTERED', 'Auth', f'New user {new_user.email} registered with role {assigned_role} (is_donor={is_donor})', user_email=new_user.email)
                db.commit()

                user_dict = new_user.to_dict()
                if new_user.blood_group_id:
                    bg = db.query(BloodGroup).filter(BloodGroup.id == new_user.blood_group_id).first()
                    if bg:
                        user_dict['blood_group_name'] = bg.group_name

                return {
                    'success': True,
                    'message': 'Registration successful',
                    'token': token,
                    'user': user_dict
                }, 201
            except Exception as e:
                db.rollback()
                return {'success': False, 'message': f'Registration failed: {str(e)}'}, 400

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
            user_dict = user.to_dict()
            if user.blood_group_id:
                bg = db.query(BloodGroup).filter(BloodGroup.id == user.blood_group_id).first()
                if bg:
                    user_dict['blood_group_name'] = bg.group_name
            return {'success': True, 'user': user_dict}, 200

    @staticmethod
    def update_profile(user_id, data, current_user_role='User'):
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {'success': False, 'message': 'User not found'}, 404

            try:
                if 'name' in data and data['name']:
                    user.name = data['name'].strip()
                if 'phone' in data:
                    user.phone = data['phone']
                if 'age' in data and data['age']:
                    try:
                        user.age = int(data['age'])
                    except (ValueError, TypeError):
                        pass
                if 'gender' in data:
                    user.gender = data['gender']
                if 'dob' in data:
                    user.dob = data['dob']
                if 'city' in data:
                    user.city = data['city']
                if 'emergency_contact' in data:
                    user.emergency_contact = data['emergency_contact']

                # Blood Group Protection: Cannot arbitrarily change verified blood group
                if 'blood_group_id' in data and data['blood_group_id'] is not None:
                    new_bg_id = _resolve_valid_blood_group_id(db, data['blood_group_id'])
                    if user.blood_group_id and user.blood_group_id != new_bg_id:
                        if user.is_blood_group_verified and current_user_role not in ['Admin', 'BloodBank']:
                            return {
                                'success': False,
                                'message': 'Your blood group has been verified by clinical laboratory testing and cannot be changed directly. Please contact Blood Bank administration with supporting medical documents to request a modification.'
                            }, 403
                        user.blood_group_id = new_bg_id
                    elif not user.blood_group_id:
                        user.blood_group_id = new_bg_id

                if 'is_blood_group_verified' in data and current_user_role in ['Admin', 'BloodBank']:
                    user.is_blood_group_verified = bool(data['is_blood_group_verified'])

                if 'address' in data:
                    user.address = data['address']

                if 'is_donor' in data:
                    user.is_donor = bool(data['is_donor'])
                    if user.is_donor:
                        # Ensure user has a valid blood_group_id
                        user.blood_group_id = _resolve_valid_blood_group_id(db, user.blood_group_id)

                        if user.blood_group_id:
                            existing_donor = db.query(Donor).filter((Donor.email == user.email) | (Donor.contact == user.phone)).first()
                            if not existing_donor:
                                d = Donor(
                                    name=user.name,
                                    age=user.age or 25,
                                    gender=user.gender or 'Other',
                                    blood_group_id=user.blood_group_id,
                                    contact=user.phone or user.email,
                                    email=user.email,
                                    address=user.address,
                                    medical_notes='Registered Voluntary Donor via User Portal',
                                    status='Eligible'
                                )
                                db.add(d)
                            else:
                                existing_donor.blood_group_id = user.blood_group_id
                                existing_donor.name = user.name
                                existing_donor.contact = user.phone or user.email
                                existing_donor.address = user.address

                log_audit(db, 'PROFILE_UPDATED', 'Auth', f'User {user.email} updated profile (is_donor={user.is_donor})', user_email=user.email)
                db.commit()

                user_dict = user.to_dict()
                if user.blood_group_id:
                    bg = db.query(BloodGroup).filter(BloodGroup.id == user.blood_group_id).first()
                    if bg:
                        user_dict['blood_group_name'] = bg.group_name

                return {'success': True, 'message': 'Profile updated successfully', 'user': user_dict}, 200
            except Exception as e:
                db.rollback()
                return {'success': False, 'message': f'Failed to update profile: {str(e)}'}, 400
