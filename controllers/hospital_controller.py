from database import get_db
from models import Hospital, Patient, BloodRequest
from auth_utils import log_audit

class HospitalController:
    @staticmethod
    def list_hospitals(search='', hospital_type=''):
        with get_db() as db:
            query = db.query(Hospital)
            if search:
                query = query.filter((Hospital.name.ilike(f'%{search}%')) | (Hospital.phone.ilike(f'%{search}%')) | (Hospital.email.ilike(f'%{search}%')) | (Hospital.address.ilike(f'%{search}%')))
            if hospital_type:
                query = query.filter(Hospital.hospital_type == hospital_type)

            hospitals = query.order_by(Hospital.name.asc()).all()
            return {
                'success': True,
                'count': len(hospitals),
                'hospitals': [h.to_dict() for h in hospitals]
            }, 200

    @staticmethod
    def create_hospital(data):
        name = (data.get('name') or '').strip()
        address = (data.get('address') or '').strip()
        phone = (data.get('phone') or '').strip()
        email = (data.get('email') or '').strip().lower()

        if not name or not address or not phone or not email:
            return {'success': False, 'message': 'Name, Address, Phone, and Email are required'}, 400

        with get_db() as db:
            hospital = Hospital(
                name=name,
                license_no=data.get('license_no'),
                address=address,
                phone=phone,
                email=email,
                contact_person=data.get('contact_person'),
                hospital_type=data.get('hospital_type', 'General'),
                is_active=data.get('is_active', True)
            )
            db.add(hospital)
            db.flush()
            log_audit(db, 'HOSPITAL_CREATED', 'Hospital', f'Registered hospital {name}')
            db.commit()

            return {
                'success': True,
                'message': 'Hospital added successfully',
                'hospital': hospital.to_dict()
            }, 201

    @staticmethod
    def get_hospital(hospital_id):
        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            patients = db.query(Patient).filter(Patient.hospital_id == hospital_id).all()
            requests = db.query(BloodRequest).filter(BloodRequest.hospital_id == hospital_id).all()

            h_dict = hosp.to_dict()
            h_dict['total_patients'] = len(patients)
            h_dict['total_requests'] = len(requests)
            h_dict['recent_requests'] = [r.to_dict() for r in requests[:5]]

            return {'success': True, 'hospital': h_dict}, 200

    @staticmethod
    def update_hospital(hospital_id, data):
        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            if 'name' in data and data['name']:
                hosp.name = data['name'].strip()
            if 'license_no' in data:
                hosp.license_no = data['license_no']
            if 'address' in data and data['address']:
                hosp.address = data['address'].strip()
            if 'phone' in data and data['phone']:
                hosp.phone = data['phone'].strip()
            if 'email' in data and data['email']:
                hosp.email = data['email'].strip().lower()
            if 'contact_person' in data:
                hosp.contact_person = data['contact_person']
            if 'hospital_type' in data:
                hosp.hospital_type = data['hospital_type']
            if 'is_active' in data:
                hosp.is_active = bool(data['is_active'])

            log_audit(db, 'HOSPITAL_UPDATED', 'Hospital', f'Updated hospital {hosp.name} (id: {hospital_id})')
            db.commit()

            return {'success': True, 'message': 'Hospital updated successfully', 'hospital': hosp.to_dict()}, 200

    @staticmethod
    def delete_hospital(hospital_id):
        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            name = hosp.name
            db.delete(hosp)
            log_audit(db, 'HOSPITAL_DELETED', 'Hospital', f'Deleted hospital {name} (id: {hospital_id})')
            db.commit()

            return {'success': True, 'message': f'Hospital {name} deleted successfully'}, 200
