from datetime import datetime, timezone
from database import get_db
from models import BloodBankProfile, User
from auth_utils import log_audit

class BloodBankProfileController:
    @staticmethod
    def get_profile():
        with get_db() as db:
            profile = db.query(BloodBankProfile).first()
            if not profile:
                profile = BloodBankProfile(
                    bank_name='LSB² Central Blood Bank & Transfusion Center',
                    license_number='BB-LIC-2026-98764',
                    bank_type='Central Transfusion Center',
                    operating_hours='24/7 Emergency & Transfusion Services',
                    contact_person='Dr. Robert Hayes, MD',
                    phone='+1 (555) 987-6543',
                    emergency_helpline='+1 (800) 555-BLOOD',
                    email='contact@lsb2-bloodbank.org',
                    website='https://lsb2-bloodbank.org',
                    address='450 Metro Health Boulevard, Medical District Suite 300',
                    city='Metropolis',
                    state='State',
                    verification_status='Verified'
                )
                db.add(profile)
                db.commit()

            staff_users = db.query(User).filter(User.role.in_(['BloodBank', 'Admin', 'Staff'])).all()

            return {
                'success': True,
                'profile': profile.to_dict(),
                'staff': [
                    {
                        'id': u.id,
                        'name': u.name,
                        'email': u.email,
                        'role': u.role,
                        'phone': u.phone,
                        'status': u.status
                    } for u in staff_users
                ]
            }, 200

    @staticmethod
    def update_profile(data):
        with get_db() as db:
            profile = db.query(BloodBankProfile).first()
            if not profile:
                profile = BloodBankProfile()
                db.add(profile)

            if 'bank_name' in data: profile.bank_name = data['bank_name'].strip()
            if 'license_number' in data: profile.license_number = data['license_number'].strip()
            if 'bank_type' in data: profile.bank_type = data['bank_type']
            if 'operating_hours' in data: profile.operating_hours = data['operating_hours']
            if 'contact_person' in data: profile.contact_person = data['contact_person'].strip()
            if 'phone' in data: profile.phone = data['phone'].strip()
            if 'emergency_helpline' in data: profile.emergency_helpline = data['emergency_helpline'].strip()
            if 'email' in data: profile.email = data['email'].strip()
            if 'website' in data: profile.website = data['website'].strip()
            if 'address' in data: profile.address = data['address'].strip()
            if 'city' in data: profile.city = data['city'].strip()
            if 'state' in data: profile.state = data['state'].strip()
            if 'postal_code' in data: profile.postal_code = data['postal_code'].strip()
            if 'verification_status' in data: profile.verification_status = data['verification_status']
            if 'verification_docs' in data: profile.verification_docs = data['verification_docs']
            if 'total_capacity_units' in data: profile.total_capacity_units = int(data['total_capacity_units'])

            profile.updated_at = datetime.now(timezone.utc)
            log_audit(db, 'PROFILE_UPDATED', 'BloodBankProfile', f"Updated Blood Bank organizational profile for {profile.bank_name}")
            db.commit()

            return {
                'success': True,
                'message': 'Blood bank profile updated successfully',
                'profile': profile.to_dict()
            }, 200
