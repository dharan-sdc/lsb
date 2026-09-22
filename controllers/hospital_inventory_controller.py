from datetime import datetime, timezone
from database import get_db
from models import HospitalInventory, Hospital, BloodGroup, User
from auth_utils import log_audit, create_notification

class HospitalInventoryController:
    @staticmethod
    def get_inventory(hospital_id):
        if not hospital_id:
            return {'success': False, 'message': 'Hospital ID is required'}, 400

        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            # Ensure all 8 blood groups have an inventory record for this hospital
            blood_groups = db.query(BloodGroup).all()
            existing_inv = db.query(HospitalInventory).filter(HospitalInventory.hospital_id == hospital_id).all()
            existing_map = {inv.blood_group_id: inv for inv in existing_inv}

            for bg in blood_groups:
                if bg.id not in existing_map:
                    new_item = HospitalInventory(
                        hospital_id=hospital_id,
                        blood_group_id=bg.id,
                        units_available=0,
                        total_ml=0.0,
                        low_stock_threshold=3
                    )
                    db.add(new_item)
            db.commit()

            # Refresh
            inv_list = db.query(HospitalInventory).filter(
                HospitalInventory.hospital_id == hospital_id
            ).join(BloodGroup).order_by(BloodGroup.id).all()

            total_units = sum(i.units_available for i in inv_list)
            low_stock_count = sum(1 for i in inv_list if i.units_available <= i.low_stock_threshold)

            return {
                'success': True,
                'hospital': hosp.to_dict(),
                'total_units': total_units,
                'low_stock_count': low_stock_count,
                'inventory': [i.to_dict() for i in inv_list]
            }, 200

    @staticmethod
    def adjust_stock(hospital_id, data, user_email='hospital@bloodbank.com'):
        blood_group_id = data.get('blood_group_id')
        units = data.get('units')
        action = data.get('action', 'add')  # add, subtract, set
        threshold = data.get('low_stock_threshold')
        fridge = data.get('storage_fridge')

        if not hospital_id or not blood_group_id or units is None:
            return {'success': False, 'message': 'Hospital ID, Blood Group ID, and Units are required'}, 400

        try:
            blood_group_id = int(blood_group_id)
            units = int(units)
        except ValueError:
            return {'success': False, 'message': 'Blood Group ID and Units must be integers'}, 400

        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            item = db.query(HospitalInventory).filter(
                HospitalInventory.hospital_id == hospital_id,
                HospitalInventory.blood_group_id == blood_group_id
            ).first()

            if not item:
                item = HospitalInventory(
                    hospital_id=hospital_id,
                    blood_group_id=blood_group_id,
                    units_available=0,
                    total_ml=0.0,
                    low_stock_threshold=3
                )
                db.add(item)
                db.flush()

            old_units = item.units_available
            if action == 'add':
                item.units_available += units
            elif action == 'subtract':
                if item.units_available < units:
                    return {'success': False, 'message': f'Cannot deduct {units} units. Only {item.units_available} units available in hospital stock.'}, 400
                item.units_available -= units
            elif action == 'set':
                item.units_available = max(0, units)

            item.total_ml = float(item.units_available) * 450.0
            if threshold is not None:
                try:
                    item.low_stock_threshold = max(1, int(threshold))
                except ValueError:
                    pass
            if fridge:
                item.storage_fridge = fridge.strip()

            item.last_updated = datetime.now(timezone.utc)
            bg_name = item.blood_group.group_name if item.blood_group else 'Blood'

            # Low stock notification
            if item.units_available <= item.low_stock_threshold:
                create_notification(
                    db,
                    title=f"⚠️ Hospital Low Stock Alert: {hosp.name}",
                    message=f"Hospital {hosp.name} has low stock for {bg_name} ({item.units_available} units remaining).",
                    notification_type="low_stock"
                )

            log_audit(
                db,
                action='HOSPITAL_STOCK_ADJUSTED',
                module='HospitalInventory',
                details=f'{hosp.name}: Adjusted {bg_name} stock from {old_units} to {item.units_available} units ({action})',
                user_email=user_email
            )
            db.commit()

            return {
                'success': True,
                'message': f'{hosp.name} inventory updated successfully for {bg_name}',
                'item': item.to_dict()
            }, 200

    @staticmethod
    def issue_to_patient(hospital_id, data, user_email='hospital@bloodbank.com'):
        blood_group_id = data.get('blood_group_id')
        units = data.get('units', 1)
        patient_name = (data.get('patient_name') or '').strip()
        condition = (data.get('condition') or 'In-patient transfusion').strip()
        issued_by = data.get('issued_by', 'Hospital Staff')

        if not hospital_id or not blood_group_id or not patient_name:
            return {'success': False, 'message': 'Hospital ID, Blood Group ID, and Patient Name are required'}, 400

        try:
            blood_group_id = int(blood_group_id)
            units = int(units)
        except ValueError:
            return {'success': False, 'message': 'Blood Group ID and Units must be integers'}, 400

        with get_db() as db:
            hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
            if not hosp:
                return {'success': False, 'message': 'Hospital not found'}, 404

            item = db.query(HospitalInventory).filter(
                HospitalInventory.hospital_id == hospital_id,
                HospitalInventory.blood_group_id == blood_group_id
            ).first()

            if not item or item.units_available < units:
                avail = item.units_available if item else 0
                return {'success': False, 'message': f'Insufficient hospital stock. Required: {units} units, Available: {avail} units.'}, 400

            item.units_available -= units
            item.total_ml = max(0.0, item.total_ml - (float(units) * 450.0))
            item.last_updated = datetime.now(timezone.utc)

            bg_name = item.blood_group.group_name if item.blood_group else 'Blood'

            create_notification(
                db,
                title=f"🏥 Hospital Patient Transfusion: {hosp.name}",
                message=f"Issued {units} unit(s) of {bg_name} to patient {patient_name} ({condition}) by {issued_by}.",
                notification_type="approval"
            )

            log_audit(
                db,
                action='HOSPITAL_PATIENT_ISSUE',
                module='HospitalInventory',
                details=f'{hosp.name}: Issued {units} unit(s) of {bg_name} for patient {patient_name} ({condition})',
                user_email=user_email
            )
            db.commit()

            return {
                'success': True,
                'message': f'Successfully issued {units} unit(s) of {bg_name} for {patient_name}',
                'remaining_units': item.units_available,
                'item': item.to_dict()
            }, 200
