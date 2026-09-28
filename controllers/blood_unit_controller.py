from datetime import datetime, timezone, timedelta, date
import random
from database import get_db
from models import BloodUnit, BloodGroup, BloodInventory, BloodRequest, BloodIssue
from auth_utils import log_audit, create_notification

class BloodUnitController:
    @staticmethod
    def list_units(blood_group_id=None, status=None, test_status=None, search='', expiring_soon=False):
        with get_db() as db:
            query = db.query(BloodUnit).join(BloodGroup)
            
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (BloodUnit.unit_code.ilike(term)) |
                    (BloodUnit.donor_name.ilike(term)) |
                    (BloodUnit.source_name.ilike(term)) |
                    (BloodUnit.storage_location.ilike(term))
                )
            
            if blood_group_id and str(blood_group_id).lower() != 'all':
                try:
                    query = query.filter(BloodUnit.blood_group_id == int(blood_group_id))
                except ValueError:
                    pass

            if status and status != 'ALL':
                query = query.filter(BloodUnit.status == status)

            if test_status and test_status != 'ALL':
                query = query.filter(BloodUnit.test_status == test_status)

            if expiring_soon:
                today = date.today()
                seven_days = today + timedelta(days=7)
                query = query.filter(BloodUnit.expiry_date >= today, BloodUnit.expiry_date <= seven_days, BloodUnit.status == 'Available')

            units = query.order_by(BloodUnit.expiry_date.asc(), BloodUnit.id.desc()).all()
            
            # Quick status counts
            all_units = db.query(BloodUnit).all()
            today = date.today()
            available_count = sum(1 for u in all_units if u.status == 'Available')
            testing_count = sum(1 for u in all_units if u.status == 'Testing' or u.test_status == 'Pending')
            quarantine_count = sum(1 for u in all_units if u.status == 'Quarantine')
            expiring_count = sum(1 for u in all_units if u.status == 'Available' and 0 <= (u.expiry_date - today).days <= 7)
            reserved_count = sum(1 for u in all_units if u.status == 'Reserved')
            issued_count = sum(1 for u in all_units if u.status == 'Issued')

            return {
                'success': True,
                'count': len(units),
                'stats': {
                    'total': len(all_units),
                    'available': available_count,
                    'testing': testing_count,
                    'quarantine': quarantine_count,
                    'expiring_soon': expiring_count,
                    'reserved': reserved_count,
                    'issued': issued_count
                },
                'units': [u.to_dict() for u in units]
            }, 200

    @staticmethod
    def get_unit(unit_id):
        with get_db() as db:
            unit = db.query(BloodUnit).filter(BloodUnit.id == unit_id).first()
            if not unit:
                return {'success': False, 'message': 'Blood unit not found'}, 404
            return {'success': True, 'unit': unit.to_dict()}, 200

    @staticmethod
    def create_unit(data):
        blood_group_id = data.get('blood_group_id')
        if not blood_group_id:
            return {'success': False, 'message': 'Blood group is required'}, 400

        try:
            bg_id = int(blood_group_id)
        except ValueError:
            return {'success': False, 'message': 'Invalid blood group ID'}, 400

        today = date.today()
        col_date = today
        if data.get('collection_date'):
            try:
                col_date = datetime.strptime(data['collection_date'][:10], '%Y-%m-%d').date()
            except ValueError:
                pass

        exp_date = col_date + timedelta(days=42)
        if data.get('expiry_date'):
            try:
                exp_date = datetime.strptime(data['expiry_date'][:10], '%Y-%m-%d').date()
            except ValueError:
                pass

        unit_code = data.get('unit_code') or f"BU-{datetime.now(timezone.utc).year}-{random.randint(100000, 999999)}"
        initial_status = data.get('status', 'Available')
        test_status = data.get('test_status', 'Passed' if initial_status == 'Available' else 'Pending')

        with get_db() as db:
            # Check unique unit code
            existing = db.query(BloodUnit).filter(BloodUnit.unit_code == unit_code).first()
            if existing:
                unit_code = f"BU-{datetime.now(timezone.utc).year}-{random.randint(100000, 999999)}"

            unit = BloodUnit(
                unit_code=unit_code,
                blood_group_id=bg_id,
                donation_id=data.get('donation_id'),
                camp_id=data.get('camp_id'),
                donor_name=data.get('donor_name', 'Voluntary Donor'),
                volume_ml=float(data.get('volume_ml', 450.0)),
                collection_date=col_date,
                expiry_date=exp_date,
                source_type=data.get('source_type', 'Center Walk-in'),
                source_name=data.get('source_name', 'Central Blood Bank'),
                storage_location=data.get('storage_location', 'Main Blood Bank Fridge - Rack A'),
                status=initial_status,
                test_status=test_status,
                hiv_test=data.get('hiv_test', 'Negative'),
                hbsag_test=data.get('hbsag_test', 'Negative'),
                hcv_test=data.get('hcv_test', 'Negative'),
                vdrl_test=data.get('vdrl_test', 'Negative'),
                malaria_test=data.get('malaria_test', 'Negative'),
                abo_rh_confirmed=data.get('abo_rh_confirmed', 'Confirmed'),
                tested_by=data.get('tested_by', 'Medical Officer')
            )
            db.add(unit)
            db.flush()

            # If created as Available, sync central inventory
            if initial_status == 'Available':
                inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == bg_id).first()
                if inv:
                    inv.units_available += 1
                    inv.total_ml += unit.volume_ml
                    inv.last_updated = datetime.now(timezone.utc)

            log_audit(db, 'UNIT_CREATED', 'BloodUnit', f"Created blood unit {unit.unit_code} ({unit.blood_group.group_name if unit.blood_group else bg_id}) - Status: {initial_status}")
            db.commit()

            return {
                'success': True,
                'message': f"Blood Unit {unit.unit_code} logged successfully",
                'unit': unit.to_dict()
            }, 201

    @staticmethod
    def update_testing_approval(unit_id, data):
        """Processes testing results and moves blood unit from Testing/Quarantine to Available or Discarded."""
        with get_db() as db:
            unit = db.query(BloodUnit).filter(BloodUnit.id == unit_id).first()
            if not unit:
                return {'success': False, 'message': 'Blood unit not found'}, 404

            prev_status = unit.status
            new_test_status = data.get('test_status', unit.test_status)  # Passed, Failed, Quarantined
            
            unit.test_status = new_test_status
            if 'hiv_test' in data: unit.hiv_test = data['hiv_test']
            if 'hbsag_test' in data: unit.hbsag_test = data['hbsag_test']
            if 'hcv_test' in data: unit.hcv_test = data['hcv_test']
            if 'vdrl_test' in data: unit.vdrl_test = data['vdrl_test']
            if 'malaria_test' in data: unit.malaria_test = data['malaria_test']
            if 'abo_rh_confirmed' in data: unit.abo_rh_confirmed = data['abo_rh_confirmed']
            if 'tested_by' in data: unit.tested_by = data['tested_by']
            if 'test_notes' in data: unit.test_notes = data['test_notes']
            unit.tested_at = datetime.now(timezone.utc)

            if new_test_status == 'Passed':
                unit.status = 'Available'
                # If was not available before, increment central inventory
                if prev_status != 'Available':
                    inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == unit.blood_group_id).first()
                    if inv:
                        inv.units_available += 1
                        inv.total_ml += unit.volume_ml
                        inv.last_updated = datetime.now(timezone.utc)
            elif new_test_status == 'Failed':
                unit.status = 'Discarded'
                unit.discard_reason = data.get('test_notes') or 'Failed standard viral/serological testing screening'
                # If was previously counted in available, deduct
                if prev_status == 'Available':
                    inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == unit.blood_group_id).first()
                    if inv and inv.units_available > 0:
                        inv.units_available -= 1
                        inv.total_ml -= unit.volume_ml
                        inv.last_updated = datetime.now(timezone.utc)
            elif new_test_status == 'Quarantined':
                unit.status = 'Quarantine'

            log_audit(db, 'UNIT_TEST_UPDATED', 'BloodTesting', f"Test results for Unit {unit.unit_code}: {new_test_status} -> Status: {unit.status}")
            db.commit()

            return {
                'success': True,
                'message': f"Testing results recorded. Unit is now {unit.status}.",
                'unit': unit.to_dict()
            }, 200

    @staticmethod
    def discard_unit(unit_id, reason):
        with get_db() as db:
            unit = db.query(BloodUnit).filter(BloodUnit.id == unit_id).first()
            if not unit:
                return {'success': False, 'message': 'Blood unit not found'}, 404

            prev_status = unit.status
            unit.status = 'Discarded'
            unit.discard_reason = reason or 'Expired or damaged storage container'

            if prev_status == 'Available':
                inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == unit.blood_group_id).first()
                if inv and inv.units_available > 0:
                    inv.units_available -= 1
                    inv.total_ml -= unit.volume_ml
                    inv.last_updated = datetime.now(timezone.utc)

            log_audit(db, 'UNIT_DISCARDED', 'BloodUnit', f"Discarded unit {unit.unit_code}. Reason: {unit.discard_reason}")
            db.commit()

            return {
                'success': True,
                'message': f"Unit {unit.unit_code} marked as Discarded",
                'unit': unit.to_dict()
            }, 200
