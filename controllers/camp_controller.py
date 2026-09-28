from datetime import datetime, timezone, date, timedelta
import random
from database import get_db
from models import BloodCamp, CampRegistration, BloodGroup, User, BloodDonation, BloodInventory, Donor
from auth_utils import log_audit, create_notification

class CampController:
    @staticmethod
    def list_camps(search='', status='', start_date='', end_date=''):
        with get_db() as db:
            query = db.query(BloodCamp)
            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    (BloodCamp.name.ilike(term)) |
                    (BloodCamp.camp_code.ilike(term)) |
                    (BloodCamp.location.ilike(term)) |
                    (BloodCamp.organizer.ilike(term)) |
                    (BloodCamp.city.ilike(term))
                )
            if status and status != 'ALL':
                query = query.filter(BloodCamp.status == status)
            
            camps = query.order_by(BloodCamp.camp_date.desc()).all()
            return {
                'success': True,
                'count': len(camps),
                'camps': [c.to_dict() for c in camps]
            }, 200

    @staticmethod
    def get_camp(camp_id):
        with get_db() as db:
            camp = db.query(BloodCamp).filter(BloodCamp.id == camp_id).first()
            if not camp:
                return {'success': False, 'message': 'Blood camp not found'}, 404
            
            regs = db.query(CampRegistration).filter(CampRegistration.camp_id == camp_id).order_by(CampRegistration.id.desc()).all()
            camp_dict = camp.to_dict()
            camp_dict['registrations'] = [r.to_dict() for r in regs]
            return {
                'success': True,
                'camp': camp_dict
            }, 200

    @staticmethod
    def create_camp(data):
        name = data.get('name', '').strip()
        organizer = data.get('organizer', '').strip()
        location = data.get('location', '').strip()
        camp_date_str = data.get('camp_date')

        if not name or not organizer or not location or not camp_date_str:
            return {'success': False, 'message': 'Camp Name, Organizer, Location, and Date are required'}, 400

        try:
            camp_date = datetime.strptime(camp_date_str[:10], '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'message': 'Invalid date format (use YYYY-MM-DD)'}, 400

        camp_code = f"CMP-{datetime.now(timezone.utc).year}-{random.randint(1000, 9999)}"

        with get_db() as db:
            new_camp = BloodCamp(
                camp_code=camp_code,
                name=name,
                organizer=organizer,
                camp_date=camp_date,
                start_time=data.get('start_time', '09:00 AM'),
                end_time=data.get('end_time', '05:00 PM'),
                location=location,
                address=data.get('address', ''),
                city=data.get('city', 'Metropolis'),
                state=data.get('state', 'State'),
                map_link=data.get('map_link'),
                contact_person=data.get('contact_person'),
                contact_phone=data.get('contact_phone'),
                contact_email=data.get('contact_email'),
                capacity=int(data.get('capacity', 100)),
                target_units=int(data.get('target_units', 50)),
                description=data.get('description'),
                instructions=data.get('instructions'),
                status='Upcoming'
            )
            db.add(new_camp)
            db.flush()

            log_audit(db, 'CAMP_CREATED', 'BloodCamp', f"Created blood camp '{name}' ({camp_code}) scheduled for {camp_date}")
            create_notification(
                db,
                title=f"🏕️ New Blood Camp Scheduled: {name}",
                message=f"A new blood camp organized by {organizer} is scheduled for {camp_date} at {location}.",
                notification_type="camp_created"
            )
            db.commit()

            return {
                'success': True,
                'message': f"Blood camp '{name}' created successfully",
                'camp': new_camp.to_dict()
            }, 201

    @staticmethod
    def update_camp(camp_id, data):
        with get_db() as db:
            camp = db.query(BloodCamp).filter(BloodCamp.id == camp_id).first()
            if not camp:
                return {'success': False, 'message': 'Camp not found'}, 404

            if 'name' in data: camp.name = data['name'].strip()
            if 'organizer' in data: camp.organizer = data['organizer'].strip()
            if 'location' in data: camp.location = data['location'].strip()
            if 'address' in data: camp.address = data['address'].strip()
            if 'city' in data: camp.city = data['city'].strip()
            if 'state' in data: camp.state = data['state'].strip()
            if 'start_time' in data: camp.start_time = data['start_time']
            if 'end_time' in data: camp.end_time = data['end_time']
            if 'contact_person' in data: camp.contact_person = data['contact_person']
            if 'contact_phone' in data: camp.contact_phone = data['contact_phone']
            if 'contact_email' in data: camp.contact_email = data['contact_email']
            if 'capacity' in data: camp.capacity = int(data['capacity'])
            if 'target_units' in data: camp.target_units = int(data['target_units'])
            if 'description' in data: camp.description = data['description']
            if 'instructions' in data: camp.instructions = data['instructions']
            if 'status' in data: camp.status = data['status']
            if 'collected_units' in data: camp.collected_units = int(data['collected_units'])
            if 'camp_date' in data and data['camp_date']:
                try:
                    camp.camp_date = datetime.strptime(data['camp_date'][:10], '%Y-%m-%d').date()
                except ValueError:
                    pass

            log_audit(db, 'CAMP_UPDATED', 'BloodCamp', f"Updated blood camp details for {camp.camp_code} ({camp.name})")
            db.commit()

            return {
                'success': True,
                'message': 'Camp updated successfully',
                'camp': camp.to_dict()
            }, 200

    @staticmethod
    def delete_camp(camp_id):
        with get_db() as db:
            camp = db.query(BloodCamp).filter(BloodCamp.id == camp_id).first()
            if not camp:
                return {'success': False, 'message': 'Camp not found'}, 404

            code = camp.camp_code
            name = camp.name
            db.delete(camp)
            log_audit(db, 'CAMP_DELETED', 'BloodCamp', f"Deleted blood camp {code} ({name})")
            db.commit()

            return {'success': True, 'message': f"Blood camp '{name}' removed"}, 200

    @staticmethod
    def register_donor_for_camp(camp_id, data, user_id=None):
        with get_db() as db:
            camp = db.query(BloodCamp).filter(BloodCamp.id == camp_id).first()
            if not camp:
                return {'success': False, 'message': 'Camp not found'}, 404

            donor_name = data.get('donor_name', '').strip()
            donor_phone = data.get('donor_phone', '').strip()
            donor_email = data.get('donor_email', '').strip()
            blood_group_id = data.get('blood_group_id')
            age = data.get('age')
            gender = data.get('gender')

            if not donor_name:
                if user_id:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        donor_name = user.name
                        donor_phone = donor_phone or user.phone or ''
                        donor_email = donor_email or user.email or ''
                        blood_group_id = blood_group_id or user.blood_group_id
                        age = age or user.age
                        gender = gender or user.gender
                else:
                    return {'success': False, 'message': 'Donor name is required'}, 400

            # 1. BACKEND COOLDOWN VALIDATION: Check last completed donation date
            last_date = None
            if user_id:
                last_donation = db.query(BloodDonation).filter(
                    BloodDonation.user_id == user_id,
                    BloodDonation.status == 'Completed'
                ).order_by(BloodDonation.donation_date.desc()).first()
                if last_donation and last_donation.donation_date:
                    last_date = last_donation.donation_date

            if not last_date and (donor_email or donor_phone):
                donor_obj = db.query(Donor).filter(
                    (Donor.email == donor_email) | (Donor.contact == donor_phone)
                ).first()
                if donor_obj and donor_obj.last_donation_date:
                    last_date = donor_obj.last_donation_date

            if last_date:
                cooldown_days = 90  # Standard whole-blood medical cooldown
                next_eligible_date = last_date + timedelta(days=cooldown_days)
                today = date.today()
                
                # If current date or camp date is before next eligible date, reject registration on backend
                if today < next_eligible_date or (camp.camp_date and camp.camp_date < next_eligible_date):
                    days_remaining = max(1, (next_eligible_date - today).days)
                    return {
                        'success': False,
                        'message': f"Registration rejected: You are currently in the 90-day medical donation cooldown following your donation on {last_date.strftime('%d %b %Y')}. Your next eligible donation date is {next_eligible_date.strftime('%d %b %Y')} ({days_remaining} day{'s' if days_remaining > 1 else ''} remaining).",
                        'is_eligible': False,
                        'reason': 'Donation Cooldown Active',
                        'last_donation_date': last_date.isoformat(),
                        'next_eligible_date': next_eligible_date.isoformat(),
                        'days_remaining': days_remaining
                    }, 400

            # 2. Check duplicate registration for same user / email in this camp
            existing = db.query(CampRegistration).filter(
                CampRegistration.camp_id == camp_id,
                CampRegistration.status != 'Cancelled',
                (CampRegistration.user_id == user_id) | (CampRegistration.donor_email == donor_email)
            ).first() if (user_id or donor_email) else None

            if existing:
                return {
                    'success': True,
                    'message': 'You are already registered for this blood camp!',
                    'registration': existing.to_dict()
                }, 200

            reg_code = f"REG-CMP{camp.id:03d}-{random.randint(100, 999)}"

            reg = CampRegistration(
                camp_id=camp_id,
                user_id=user_id,
                donor_name=donor_name,
                donor_phone=donor_phone,
                donor_email=donor_email,
                blood_group_id=int(blood_group_id) if blood_group_id else None,
                age=int(age) if age else None,
                gender=gender,
                registration_code=reg_code,
                status='Registered'
            )
            db.add(reg)
            db.flush()

            log_audit(db, 'CAMP_DONOR_REGISTERED', 'BloodCamp', f"Donor '{donor_name}' registered for camp {camp.camp_code} (Pass: {reg_code})")
            create_notification(
                db,
                title=f"🏕️ Camp Registration Confirmed: {camp.name}",
                message=f"You are registered for {camp.name} on {camp.camp_date}. Your Digital Pass Code is {reg_code}.",
                notification_type="camp_registration"
            )
            db.commit()

            return {
                'success': True,
                'message': f"Successfully registered for {camp.name}!",
                'registration': reg.to_dict()
            }, 201

    @staticmethod
    def cancel_registration(reg_id, user_id=None, user_role='User'):
        with get_db() as db:
            query = db.query(CampRegistration).filter(CampRegistration.id == reg_id)
            if user_role not in ['Admin', 'BloodBank'] and user_id:
                query = query.filter(CampRegistration.user_id == user_id)

            reg = query.first()
            if not reg:
                return {'success': False, 'message': 'Camp registration not found or unauthorized'}, 404

            reg.status = 'Cancelled'
            log_audit(db, 'CAMP_REGISTRATION_CANCELLED', 'BloodCamp', f"Registration {reg.registration_code} cancelled for camp ID {reg.camp_id}")
            db.commit()

            return {
                'success': True,
                'message': 'Camp registration has been successfully cancelled.',
                'registration': reg.to_dict()
            }, 200

    @staticmethod
    def update_screening_status(reg_id, data):
        with get_db() as db:
            reg = db.query(CampRegistration).filter(CampRegistration.id == reg_id).first()
            if not reg:
                return {'success': False, 'message': 'Camp registration not found'}, 404

            status = data.get('status', reg.status)
            reg.status = status
            if 'blood_pressure' in data: reg.blood_pressure = data['blood_pressure']
            if 'hemoglobin' in data and data['hemoglobin']: reg.hemoglobin = float(data['hemoglobin'])
            if 'weight_kg' in data and data['weight_kg']: reg.weight_kg = float(data['weight_kg'])
            if 'temperature' in data and data['temperature']: reg.temperature = float(data['temperature'])
            if 'eligibility_notes' in data: reg.eligibility_notes = data['eligibility_notes']
            if 'blood_group_id' in data and data['blood_group_id']: reg.blood_group_id = int(data['blood_group_id'])

            if status == 'Donated':
                units = int(data.get('units_donated', 1))
                reg.units_donated = units
                u_code = f"BU-{datetime.now(timezone.utc).year}-{random.randint(100000, 999999)}"
                reg.blood_unit_code = u_code

                # Auto update camp collected count
                if reg.camp:
                    reg.camp.collected_units = (reg.camp.collected_units or 0) + units

            log_audit(db, 'CAMP_DONOR_SCREENED', 'BloodCamp', f"Screening updated for {reg.donor_name} (Code: {reg.registration_code}) -> {status}")
            db.commit()

            return {
                'success': True,
                'message': f"Screening status updated to '{status}'",
                'registration': reg.to_dict()
            }, 200

    @staticmethod
    def get_user_registrations(user_id):
        with get_db() as db:
            regs = db.query(CampRegistration).filter(CampRegistration.user_id == user_id).order_by(CampRegistration.id.desc()).all()
            return {
                'success': True,
                'count': len(regs),
                'registrations': [r.to_dict() for r in regs]
            }, 200

    @staticmethod
    def get_donor_eligibility(user_id=None, email=None, phone=None):
        with get_db() as db:
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            email = email or (user.email if user else None)
            phone = phone or (user.phone if user else None)

            # Find donations
            donations = []
            if user_id:
                donations = db.query(BloodDonation).filter(
                    BloodDonation.user_id == user_id,
                    BloodDonation.status == 'Completed'
                ).order_by(BloodDonation.donation_date.desc()).all()

            if not donations and (email or phone):
                donor = db.query(Donor).filter((Donor.email == email) | (Donor.contact == phone)).first()
                if donor:
                    donations = db.query(BloodDonation).filter(
                        BloodDonation.donor_id == donor.id,
                        BloodDonation.status == 'Completed'
                    ).order_by(BloodDonation.donation_date.desc()).all()

            total_donations = len(donations)
            last_date = donations[0].donation_date if donations else None

            # Also check donor model if total_donations was set from migration
            if user:
                donor_rec = db.query(Donor).filter((Donor.email == user.email) | (Donor.contact == user.phone)).first()
                if donor_rec:
                    total_donations = max(total_donations, donor_rec.total_donations or 0)
                    if not last_date and donor_rec.last_donation_date:
                        last_date = donor_rec.last_donation_date

            cooldown_days = 90
            today = date.today()

            if last_date:
                next_eligible_date = last_date + timedelta(days=cooldown_days)
                if today < next_eligible_date:
                    days_remaining = (next_eligible_date - today).days
                    return {
                        'success': True,
                        'is_eligible': False,
                        'status': 'Not Eligible',
                        'badge': '⏳ Cooldown Active',
                        'reason': f'Donation cooldown active (90 days required between whole blood donations).',
                        'last_donation_date': last_date.isoformat(),
                        'next_eligible_date': next_eligible_date.isoformat(),
                        'days_remaining': days_remaining,
                        'cooldown_days': cooldown_days,
                        'total_donations': total_donations,
                        'user_name': user.name if user else 'Voluntary Donor'
                    }, 200
                else:
                    return {
                        'success': True,
                        'is_eligible': True,
                        'status': 'Eligible',
                        'badge': '✅ Eligible to Donate',
                        'reason': 'You are fully eligible to donate blood at any registered blood bank or camp.',
                        'last_donation_date': last_date.isoformat(),
                        'next_eligible_date': today.isoformat(),
                        'days_remaining': 0,
                        'cooldown_days': cooldown_days,
                        'total_donations': total_donations,
                        'user_name': user.name if user else 'Voluntary Donor'
                    }, 200

            return {
                'success': True,
                'is_eligible': True,
                'status': 'Eligible',
                'badge': '⭐ First-Time Eligible',
                'reason': 'You are eligible to make your first life-saving blood donation.',
                'last_donation_date': None,
                'next_eligible_date': today.isoformat(),
                'days_remaining': 0,
                'cooldown_days': cooldown_days,
                'total_donations': 0,
                'user_name': user.name if user else 'Voluntary Donor'
            }, 200
