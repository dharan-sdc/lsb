import uuid
from datetime import datetime, timezone, date
from database import get_db
from models import BloodDonation, Donor, BloodGroup, BloodInventory, User
from auth_utils import log_audit, create_notification

class DonationController:
    @staticmethod
    def list_donations(user_id=None, donor_id=None, blood_group_id=None, date_from=None, date_to=None):
        with get_db() as db:
            query = db.query(BloodDonation)
            if user_id:
                try:
                    query = query.filter(BloodDonation.user_id == int(user_id))
                except ValueError:
                    pass
            if donor_id:
                try:
                    query = query.filter(BloodDonation.donor_id == int(donor_id))
                except ValueError:
                    pass
            if blood_group_id:
                try:
                    query = query.filter(BloodDonation.blood_group_id == int(blood_group_id))
                except ValueError:
                    pass
            if date_from:
                query = query.filter(BloodDonation.donation_date >= date_from)
            if date_to:
                query = query.filter(BloodDonation.donation_date <= date_to)

            donations = query.order_by(BloodDonation.donation_date.desc(), BloodDonation.id.desc()).all()
            return {
                'success': True,
                'count': len(donations),
                'donations': [d.to_dict() for d in donations]
            }, 200

    @staticmethod
    def register_donation(data, user_id=None, recorded_by='BloodBank Staff'):
        donor_id = data.get('donor_id')
        user_id_param = data.get('user_id') or user_id
        donor_name = data.get('donor_name')
        blood_group_id = data.get('blood_group_id')
        quantity_units = data.get('quantity_units', 1)
        quantity_ml = data.get('quantity_ml')
        donation_date_str = data.get('donation_date')

        try:
            quantity_units = int(quantity_units)
            if quantity_units <= 0:
                return {'success': False, 'message': 'Quantity units must be > 0'}, 400
        except ValueError:
            return {'success': False, 'message': 'Invalid quantity units number'}, 400

        if not quantity_ml:
            quantity_ml = float(quantity_units) * 450.0
        else:
            quantity_ml = float(quantity_ml)

        donation_date = date.today()
        if donation_date_str:
            try:
                donation_date = datetime.strptime(donation_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        with get_db() as db:
            resolved_user = None
            resolved_donor = None
            resolved_name = donor_name

            if user_id_param:
                try:
                    resolved_user = db.query(User).filter(User.id == int(user_id_param)).first()
                    if resolved_user:
                        resolved_name = resolved_user.name
                        if not blood_group_id and resolved_user.blood_group_id:
                            blood_group_id = resolved_user.blood_group_id
                except (ValueError, TypeError):
                    pass

            if donor_id:
                try:
                    resolved_donor = db.query(Donor).filter(Donor.id == int(donor_id)).first()
                    if resolved_donor:
                        resolved_name = resolved_donor.name
                        if not blood_group_id:
                            blood_group_id = resolved_donor.blood_group_id
                except (ValueError, TypeError):
                    pass

            if not resolved_name:
                resolved_name = 'Anonymous Voluntary Donor'

            if not blood_group_id:
                return {'success': False, 'message': 'Blood group is required for donation'}, 400

            try:
                blood_group_id = int(blood_group_id)
            except ValueError:
                return {'success': False, 'message': 'Invalid blood group ID'}, 400

            bg = db.query(BloodGroup).filter(BloodGroup.id == blood_group_id).first()
            if not bg:
                return {'success': False, 'message': 'Blood group not found'}, 404

            # Generate unique code
            unique_suffix = str(uuid.uuid4())[:8].upper()
            donation_code = f"DON-{donation_date.strftime('%Y%m%d')}-{unique_suffix}"

            donation = BloodDonation(
                donation_code=donation_code,
                user_id=resolved_user.id if resolved_user else None,
                donor_id=resolved_donor.id if resolved_donor else None,
                donor_name=resolved_name,
                blood_group_id=blood_group_id,
                quantity_units=quantity_units,
                quantity_ml=quantity_ml,
                donation_date=donation_date,
                blood_pressure=data.get('blood_pressure', '120/80'),
                hemoglobin=float(data.get('hemoglobin', 13.5)) if data.get('hemoglobin') else 13.5,
                pulse_rate=int(data.get('pulse_rate', 72)) if data.get('pulse_rate') else 72,
                status=data.get('status', 'Completed'),
                remarks=data.get('remarks', 'Voluntary blood donation'),
                recorded_by=recorded_by
            )
            db.add(donation)

            # 1. Increment Central Inventory
            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == blood_group_id).first()
            if not inv:
                inv = BloodInventory(
                    blood_group_id=blood_group_id,
                    units_available=quantity_units,
                    total_ml=quantity_ml,
                    low_stock_threshold=5
                )
                db.add(inv)
            else:
                inv.units_available += quantity_units
                inv.total_ml += quantity_ml
                inv.last_updated = datetime.now(timezone.utc)

            # 2. Update Donor stats if donor object exists
            if resolved_donor:
                resolved_donor.total_donations = (resolved_donor.total_donations or 0) + 1
                resolved_donor.last_donation_date = donation_date

            # 3. Notification
            create_notification(
                db,
                title=f"🩸 Donation Received: {bg.group_name} (+{quantity_units} Unit{'s' if quantity_units > 1 else ''})",
                message=f"Received {quantity_units} unit(s) ({quantity_ml} ml) of {bg.group_name} blood from {resolved_name}. Central inventory updated.",
                notification_type="donation"
            )

            # 4. Audit Log
            log_audit(db, 'DONATION_REGISTERED', 'Donation', f'Recorded donation {donation_code}: {quantity_units} unit(s) of {bg.group_name} from {resolved_name}')
            db.commit()

            return {
                'success': True,
                'message': f'Donation registered successfully! {quantity_units} unit(s) of {bg.group_name} added to central inventory.',
                'donation': donation.to_dict(),
                'updated_inventory': inv.to_dict()
            }, 201

    @staticmethod
    def get_donation(donation_id):
        with get_db() as db:
            d = db.query(BloodDonation).filter(BloodDonation.id == donation_id).first()
            if not d:
                return {'success': False, 'message': 'Donation record not found'}, 404
            return {'success': True, 'donation': d.to_dict()}, 200

    @staticmethod
    def delete_donation(donation_id):
        with get_db() as db:
            d = db.query(BloodDonation).filter(BloodDonation.id == donation_id).first()
            if not d:
                return {'success': False, 'message': 'Donation not found'}, 404

            # Revert inventory
            inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == d.blood_group_id).first()
            if inv:
                inv.units_available = max(0, inv.units_available - d.quantity_units)
                inv.total_ml = max(0.0, inv.total_ml - d.quantity_ml)

            code = d.donation_code
            db.delete(d)
            log_audit(db, 'DONATION_DELETED', 'Donation', f'Deleted donation {code} and adjusted stock')
            db.commit()

            return {'success': True, 'message': f'Donation {code} removed and inventory adjusted'}, 200
