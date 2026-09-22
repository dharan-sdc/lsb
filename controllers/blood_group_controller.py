from database import get_db
from models import BloodGroup, BloodInventory
from auth_utils import log_audit

class BloodGroupController:
    COMPATIBILITY_DATA = {
        'A+': {'can_donate_to': 'A+, AB+', 'can_receive_from': 'A+, A-, O+, O-'},
        'A-': {'can_donate_to': 'A+, A-, AB+, AB-', 'can_receive_from': 'A-, O-'},
        'B+': {'can_donate_to': 'B+, AB+', 'can_receive_from': 'B+, B-, O+, O-'},
        'B-': {'can_donate_to': 'B+, B-, AB+, AB-', 'can_receive_from': 'B-, O-'},
        'AB+': {'can_donate_to': 'AB+ (Universal Receiver)', 'can_receive_from': 'All Blood Groups'},
        'AB-': {'can_donate_to': 'AB+, AB-', 'can_receive_from': 'AB-, A-, B-, O-'},
        'O+': {'can_donate_to': 'O+, A+, B+, AB+', 'can_receive_from': 'O+, O-'},
        'O-': {'can_donate_to': 'All Blood Groups (Universal Donor)', 'can_receive_from': 'O- only'},
    }

    @staticmethod
    def list_blood_groups():
        with get_db() as db:
            groups = db.query(BloodGroup).order_by(BloodGroup.id.asc()).all()
            return {
                'success': True,
                'count': len(groups),
                'blood_groups': [g.to_dict() for g in groups]
            }, 200

    @staticmethod
    def get_blood_group(group_id):
        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == group_id).first()
            if not bg:
                return {'success': False, 'message': 'Blood Group not found'}, 404
            return {'success': True, 'blood_group': bg.to_dict()}, 200

    @staticmethod
    def create_blood_group(data):
        group_name = (data.get('group_name') or '').strip().upper()
        rh_factor = (data.get('rh_factor') or '').strip()

        if not group_name or not rh_factor:
            return {'success': False, 'message': 'Group name and Rh factor are required'}, 400

        with get_db() as db:
            if db.query(BloodGroup).filter(BloodGroup.group_name == group_name).first():
                return {'success': False, 'message': f'Blood Group {group_name} already exists'}, 409

            compat = BloodGroupController.COMPATIBILITY_DATA.get(group_name, {})
            bg = BloodGroup(
                group_name=group_name,
                rh_factor=rh_factor,
                description=data.get('description', f'Blood type {group_name}'),
                can_donate_to=data.get('can_donate_to', compat.get('can_donate_to', '')),
                can_receive_from=data.get('can_receive_from', compat.get('can_receive_from', ''))
            )
            db.add(bg)
            db.flush()

            # Create corresponding inventory record
            inv = BloodInventory(
                blood_group_id=bg.id,
                units_available=int(data.get('initial_units', 0)),
                total_ml=float(data.get('initial_units', 0)) * 450.0,
                low_stock_threshold=int(data.get('low_stock_threshold', 5))
            )
            db.add(inv)
            log_audit(db, 'BLOOD_GROUP_CREATED', 'BloodGroup', f'Created blood group {group_name}')
            db.commit()

            return {'success': True, 'message': f'Blood group {group_name} created', 'blood_group': bg.to_dict()}, 201

    @staticmethod
    def update_blood_group(group_id, data):
        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == group_id).first()
            if not bg:
                return {'success': False, 'message': 'Blood Group not found'}, 404

            if 'description' in data:
                bg.description = data['description']
            if 'can_donate_to' in data:
                bg.can_donate_to = data['can_donate_to']
            if 'can_receive_from' in data:
                bg.can_receive_from = data['can_receive_from']

            log_audit(db, 'BLOOD_GROUP_UPDATED', 'BloodGroup', f'Updated blood group {bg.group_name}')
            db.commit()

            return {'success': True, 'message': 'Blood group updated successfully', 'blood_group': bg.to_dict()}, 200

    @staticmethod
    def delete_blood_group(group_id):
        with get_db() as db:
            bg = db.query(BloodGroup).filter(BloodGroup.id == group_id).first()
            if not bg:
                return {'success': False, 'message': 'Blood Group not found'}, 404

            name = bg.group_name
            db.delete(bg)
            log_audit(db, 'BLOOD_GROUP_DELETED', 'BloodGroup', f'Deleted blood group {name}')
            db.commit()

            return {'success': True, 'message': f'Blood group {name} deleted successfully'}, 200

    @staticmethod
    def get_compatibility():
        return {
            'success': True,
            'matrix': BloodGroupController.COMPATIBILITY_DATA
        }, 200
