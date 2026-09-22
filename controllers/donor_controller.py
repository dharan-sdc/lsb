from database import get_db
from models import Donor, BloodGroup, BloodDonation
from auth_utils import log_audit

class DonorController:
    @staticmethod
    def list_donors(search='', blood_group_id=None, status=''):
        with get_db() as db:
            query = db.query(Donor)
            if search:
                query = query.filter((Donor.name.ilike(f'%{search}%')) | (Donor.contact.ilike(f'%{search}%')) | (Donor.email.ilike(f'%{search}%')))
            if blood_group_id:
                try:
                    query = query.filter(Donor.blood_group_id == int(blood_group_id))
                except ValueError:
                    pass
            if status:
                query = query.filter(Donor.status == status)

            donors = query.order_by(Donor.id.desc()).all()
            return {
                'success': True,
                'count': len(donors),
                'donors': [d.to_dict() for d in donors]
            }, 200

    @staticmethod
    def create_donor(data):
        name = (data.get('name') or '').strip()
        age = data.get('age')
        gender = data.get('gender')
        blood_group_id = data.get('blood_group_id')
        contact = (data.get('contact') or '').strip()

        if not name or not age or not gender or not blood_group_id or not contact:
            return {'success': False, 'message': 'Name, Age, Gender, Blood Group, and Contact are required'}, 400

        try:
            age = int(age)
            blood_group_id = int(blood_group_id)
        except ValueError:
            return {'success': False, 'message': 'Age and Blood Group ID must be integers'}, 400

        if age < 18 or age > 65:
            eligibility_status = 'Ineligible'
        else:
            eligibility_status = data.get('status', 'Eligible')

        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == blood_group_id).first()
            if not bg:
                return {'success': False, 'message': 'Selected Blood Group does not exist'}, 404

            donor = Donor(
                name=name,
                age=age,
                gender=gender,
                blood_group_id=blood_group_id,
                contact=contact,
                email=data.get('email'),
                address=data.get('address'),
                medical_notes=data.get('medical_notes'),
                status=eligibility_status
            )
            db.add(donor)
            db.flush()
            log_audit(db, 'DONOR_CREATED', 'Donor', f'Registered donor {name} ({bg.group_name})')
            db.commit()

            return {
                'success': True,
                'message': 'Donor registered successfully',
                'donor': donor.to_dict()
            }, 201

    @staticmethod
    def get_donor(donor_id):
        with get_db() as db:
            donor = db.query(Donor).filter(Donor.id == donor_id).first()
            if not donor:
                return {'success': False, 'message': 'Donor not found'}, 404

            donations = db.query(BloodDonation).filter(BloodDonation.donor_id == donor_id).order_by(BloodDonation.donation_date.desc()).all()
            donor_dict = donor.to_dict()
            donor_dict['donation_history'] = [d.to_dict() for d in donations]

            return {'success': True, 'donor': donor_dict}, 200

    @staticmethod
    def update_donor(donor_id, data):
        with get_db() as db:
            donor = db.query(Donor).filter(Donor.id == donor_id).first()
            if not donor:
                return {'success': False, 'message': 'Donor not found'}, 404

            if 'name' in data and data['name']:
                donor.name = data['name'].strip()
            if 'age' in data and data['age']:
                donor.age = int(data['age'])
            if 'gender' in data and data['gender']:
                donor.gender = data['gender']
            if 'blood_group_id' in data and data['blood_group_id']:
                donor.blood_group_id = int(data['blood_group_id'])
            if 'contact' in data and data['contact']:
                donor.contact = data['contact'].strip()
            if 'email' in data:
                donor.email = data['email']
            if 'address' in data:
                donor.address = data['address']
            if 'medical_notes' in data:
                donor.medical_notes = data['medical_notes']
            if 'status' in data and data['status']:
                donor.status = data['status']

            log_audit(db, 'DONOR_UPDATED', 'Donor', f'Updated donor {donor.name} (id: {donor_id})')
            db.commit()

            return {'success': True, 'message': 'Donor updated successfully', 'donor': donor.to_dict()}, 200

    @staticmethod
    def delete_donor(donor_id):
        with get_db() as db:
            donor = db.query(Donor).filter(Donor.id == donor_id).first()
            if not donor:
                return {'success': False, 'message': 'Donor not found'}, 404

            name = donor.name
            db.delete(donor)
            log_audit(db, 'DONOR_DELETED', 'Donor', f'Deleted donor {name} (id: {donor_id})')
            db.commit()

            return {'success': True, 'message': f'Donor {name} deleted successfully'}, 200
