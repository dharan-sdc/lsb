from database import get_db
from models import Patient, BloodGroup, Hospital, BloodRequest
from auth_utils import log_audit

class PatientController:
    @staticmethod
    def list_patients(search='', blood_group_id=None, hospital_id=None):
        with get_db() as db:
            query = db.query(Patient)
            if search:
                query = query.filter((Patient.name.ilike(f'%{search}%')) | (Patient.condition.ilike(f'%{search}%')) | (Patient.contact.ilike(f'%{search}%')))
            if blood_group_id:
                try:
                    query = query.filter(Patient.blood_group_id == int(blood_group_id))
                except ValueError:
                    pass
            if hospital_id:
                try:
                    query = query.filter(Patient.hospital_id == int(hospital_id))
                except ValueError:
                    pass

            patients = query.order_by(Patient.id.desc()).all()
            return {
                'success': True,
                'count': len(patients),
                'patients': [p.to_dict() for p in patients]
            }, 200

    @staticmethod
    def create_patient(data):
        name = (data.get('name') or '').strip()
        age = data.get('age')
        gender = data.get('gender')
        blood_group_id = data.get('blood_group_id')

        if not name or not age or not gender or not blood_group_id:
            return {'success': False, 'message': 'Name, Age, Gender, and Blood Group are required'}, 400

        try:
            age = int(age)
            blood_group_id = int(blood_group_id)
            hospital_id = int(data.get('hospital_id')) if data.get('hospital_id') else None
        except ValueError:
            return {'success': False, 'message': 'Invalid ID or age format'}, 400

        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == blood_group_id).first()
            if not bg:
                return {'success': False, 'message': 'Selected Blood Group does not exist'}, 404

            patient = Patient(
                name=name,
                age=age,
                gender=gender,
                blood_group_id=blood_group_id,
                hospital_id=hospital_id,
                condition=data.get('condition'),
                contact=data.get('contact'),
                address=data.get('address'),
                status=data.get('status', 'Admitted')
            )
            db.add(patient)
            db.flush()
            log_audit(db, 'PATIENT_CREATED', 'Patient', f'Admitted patient {name} ({bg.group_name})')
            db.commit()

            return {
                'success': True,
                'message': 'Patient registered successfully',
                'patient': patient.to_dict()
            }, 201

    @staticmethod
    def get_patient(patient_id):
        with get_db() as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'success': False, 'message': 'Patient not found'}, 404

            requests = db.query(BloodRequest).filter(BloodRequest.patient_id == patient_id).order_by(BloodRequest.created_at.desc()).all()
            p_dict = patient.to_dict()
            p_dict['request_history'] = [r.to_dict() for r in requests]

            return {'success': True, 'patient': p_dict}, 200

    @staticmethod
    def update_patient(patient_id, data):
        with get_db() as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'success': False, 'message': 'Patient not found'}, 404

            if 'name' in data and data['name']:
                patient.name = data['name'].strip()
            if 'age' in data and data['age']:
                patient.age = int(data['age'])
            if 'gender' in data and data['gender']:
                patient.gender = data['gender']
            if 'blood_group_id' in data and data['blood_group_id']:
                patient.blood_group_id = int(data['blood_group_id'])
            if 'hospital_id' in data:
                patient.hospital_id = int(data['hospital_id']) if data['hospital_id'] else None
            if 'condition' in data:
                patient.condition = data['condition']
            if 'contact' in data:
                patient.contact = data['contact']
            if 'address' in data:
                patient.address = data['address']
            if 'status' in data and data['status']:
                patient.status = data['status']

            log_audit(db, 'PATIENT_UPDATED', 'Patient', f'Updated patient {patient.name} (id: {patient_id})')
            db.commit()

            return {'success': True, 'message': 'Patient updated successfully', 'patient': patient.to_dict()}, 200

    @staticmethod
    def delete_patient(patient_id):
        with get_db() as db:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return {'success': False, 'message': 'Patient not found'}, 404

            name = patient.name
            db.delete(patient)
            log_audit(db, 'PATIENT_DELETED', 'Patient', f'Deleted patient {name} (id: {patient_id})')
            db.commit()

            return {'success': True, 'message': f'Patient {name} deleted successfully'}, 200
