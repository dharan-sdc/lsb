from datetime import datetime, timezone, date, timedelta
from database import get_db, init_db, engine
from models import (
    Base, User, BloodGroup, Hospital, Donor, Patient,
    BloodInventory, HospitalInventory, BloodDonation,
    BloodRequest, BloodIssue, Notification, AuditLog
)
from auth_utils import hash_password

class DatabaseSeeder:
    @staticmethod
    def seed_database():
        init_db()
        with get_db() as db:
            # 1. Standard 8 Blood Groups & Central Blood Bank Inventory
            blood_groups_data = [
                ('A+', 'Positive', 'A positive', 'A+, AB+', 'A+, A-, O+, O-', 12),
                ('A-', 'Negative', 'A negative', 'A+, A-, AB+, AB-', 'A-, O-', 4),
                ('B+', 'Positive', 'B positive', 'B+, AB+', 'B+, B-, O+, O-', 18),
                ('B-', 'Negative', 'B negative', 'B+, B-, AB+, AB-', 'B-, O-', 3),
                ('AB+', 'Positive', 'AB positive (Universal Receiver)', 'AB+', 'All Blood Groups', 10),
                ('AB-', 'Negative', 'AB negative', 'AB+, AB-', 'AB-, A-, B-, O-', 2),
                ('O+', 'Positive', 'O positive', 'O+, A+, B+, AB+', 'O+, O-', 25),
                ('O-', 'Negative', 'O negative (Universal Donor)', 'All Blood Groups', 'O- only', 5)
            ]

            for g_name, rh, desc, donate, receive, units in blood_groups_data:
                bg = db.query(BloodGroup).filter(BloodGroup.group_name == g_name).first()
                if not bg:
                    bg = BloodGroup(
                        group_name=g_name,
                        rh_factor=rh,
                        description=desc,
                        can_donate_to=donate,
                        can_receive_from=receive
                    )
                    db.add(bg)
                    db.flush()

                inv = db.query(BloodInventory).filter(BloodInventory.blood_group_id == bg.id).first()
                if not inv:
                    inv = BloodInventory(
                        blood_group_id=bg.id,
                        units_available=units,
                        total_ml=units * 450.0,
                        low_stock_threshold=5,
                        storage_fridge='Central Fridge Unit A-01'
                    )
                    db.add(inv)
                else:
                    inv.units_available = units
                    inv.total_ml = units * 450.0

            db.flush()
            bg_map = {bg.group_name: bg.id for bg in db.query(BloodGroup).all()}

            # 2. Registered Hospitals
            hospitals_data = [
                ('Metro City General Hospital', 'HOSP-2024-MC', '100 Medical Center Way, Metro City', '+1-555-4001', 'info@metrogeneral.org', 'Dr. Sarah Connor', 'Government'),
                ('St. Jude Children & Research Hospital', 'HOSP-2024-SJ', '262 Danny Thomas Place, Memphis', '+1-555-4002', 'contact@stjude-demo.org', 'Dr. Donald Thomas', 'Private'),
                ('Apex Trauma & Emergency Care', 'HOSP-2024-AP', '742 Evergreen Terrace, Apex City', '+1-555-4003', 'er@apextrauma.org', 'Nurse Chief Adams', 'Trauma Center'),
                ('Red Cross Regional Blood Center', 'HOSP-2024-RC', '431 Hope Street, Red Valley', '+1-555-4004', 'blood@redcross-demo.org', 'Coordinator Miller', 'Clinic')
            ]

            for h_name, lic, addr, phone, email, contact_p, h_type in hospitals_data:
                h = db.query(Hospital).filter(Hospital.name == h_name).first()
                if not h:
                    h = Hospital(
                        name=h_name,
                        license_no=lic,
                        address=addr,
                        phone=phone,
                        email=email,
                        contact_person=contact_p,
                        hospital_type=h_type
                    )
                    db.add(h)

            db.flush()
            hosp_map = {h.name: h.id for h in db.query(Hospital).all()}
            primary_hosp_id = hosp_map.get('Metro City General Hospital', 1)

            # 3. Pre-seed Hospital Inventories for Hospitals
            hosp_stock_presets = {
                'O+': 8, 'A+': 6, 'B+': 5, 'AB+': 3,
                'O-': 2, 'A-': 2, 'B-': 1, 'AB-': 1
            }
            for h_id in hosp_map.values():
                for bg_name, default_units in hosp_stock_presets.items():
                    if bg_name in bg_map:
                        h_inv = db.query(HospitalInventory).filter(
                            HospitalInventory.hospital_id == h_id,
                            HospitalInventory.blood_group_id == bg_map[bg_name]
                        ).first()
                        if not h_inv:
                            h_inv = HospitalInventory(
                                hospital_id=h_id,
                                blood_group_id=bg_map[bg_name],
                                units_available=default_units,
                                total_ml=float(default_units) * 450.0,
                                low_stock_threshold=3,
                                storage_fridge='Hospital Emergency Unit Fridge 1'
                            )
                            db.add(h_inv)

            # 4. Standard 4-Role Users (Admin, BloodBank, Hospital, User)
            users_data = [
                ('System Administrator', 'admin@bloodbank.com', 'Admin@123', 'Admin', '+1-555-0100', None, None, None, 'Admin HQ, Metro City', None),
                ('Central Blood Bank Operator', 'bloodbank@bloodbank.com', 'Bank@123', 'BloodBank', '+1-555-0101', None, 35, 'Other', 'Blood Bank Operations Facility', None),
                ('Metro General Hospital Coordinator', 'hospital@bloodbank.com', 'Hospital@123', 'Hospital', '+1-555-0102', primary_hosp_id, None, None, 'Metro City General Hospital Ward 4', None),
                ('Alexander Wright (Donor & Seeker)', 'user@bloodbank.com', 'User@123', 'User', '+1-555-0103', None, 28, 'Male', '12 Oak Lane, Metro City', bg_map.get('O+'))
            ]

            for name, email, pwd, role, phone, hosp_id, age, gender, addr, bg_id in users_data:
                u = db.query(User).filter(User.email == email).first()
                if not u:
                    u = User(
                        name=name,
                        email=email,
                        password_hash=hash_password(pwd),
                        role=role,
                        status='Active',
                        phone=phone,
                        hospital_id=hosp_id,
                        age=age,
                        gender=gender,
                        address=addr,
                        blood_group_id=bg_id
                    )
                    db.add(u)
                else:
                    u.role = role
                    u.hospital_id = hosp_id
                    u.blood_group_id = bg_id

            db.flush()
            user_alex = db.query(User).filter(User.email == 'user@bloodbank.com').first()

            # 5. Donors (for standard registry)
            donors_data = [
                ('Alexander Wright', 28, 'Male', 'O+', '+1-555-1101', 'user@bloodbank.com', '12 Oak Lane, Metro City', 'Fit & Healthy, regular voluntary donor', date.today() - timedelta(days=95), 3, 'Eligible'),
                ('Sophia Martinez', 34, 'Female', 'A+', '+1-555-1102', 'sophia.m@email.com', '45 Pine St, Metro City', 'Hb: 13.8, regular donor', date.today() - timedelta(days=120), 5, 'Eligible'),
                ('David Kim', 22, 'Male', 'B+', '+1-555-1103', 'david.kim@email.com', '88 Maple Ave, Metro City', 'First time donor', date.today() - timedelta(days=40), 1, 'Eligible'),
                ('Emily Watson', 45, 'Female', 'O-', '+1-555-1104', 'emily.w@email.com', '101 Cedar Blvd, Metro City', 'Universal donor volunteer', date.today() - timedelta(days=150), 8, 'Eligible'),
                ('Hannah Brown', 17, 'Female', 'A-', '+1-555-1106', 'hannah.b@email.com', '57 Birch Road, Metro City', 'Under age threshold', None, 0, 'Ineligible')
            ]

            for name, age, gender, bg_code, contact, email, addr, notes, last_date, total_d, status in donors_data:
                d = db.query(Donor).filter(Donor.name == name).first()
                if not d and bg_code in bg_map:
                    d = Donor(
                        name=name,
                        age=age,
                        gender=gender,
                        blood_group_id=bg_map[bg_code],
                        contact=contact,
                        email=email,
                        address=addr,
                        medical_notes=notes,
                        last_donation_date=last_date,
                        total_donations=total_d,
                        status=status
                    )
                    db.add(d)

            # 6. Sample User Donation
            if db.query(BloodDonation).count() == 0 and user_alex:
                sample_don = BloodDonation(
                    donation_code="DON-20241001-ALEX01",
                    user_id=user_alex.id,
                    donor_name=user_alex.name,
                    blood_group_id=bg_map.get('O+', 1),
                    quantity_units=1,
                    quantity_ml=450.0,
                    donation_date=date.today() - timedelta(days=20),
                    blood_pressure="120/80",
                    hemoglobin=14.5,
                    pulse_rate=72,
                    status="Completed",
                    remarks="Voluntary regular donation by user",
                    recorded_by="BloodBank Staff"
                )
                db.add(sample_don)

            # 7. Sample Requests (User request + Hospital request)
            if db.query(BloodRequest).count() == 0 and user_alex:
                user_req = BloodRequest(
                    request_code="REQ-20241010-USR01",
                    requester_type="User",
                    user_id=user_alex.id,
                    patient_name="Alexander Wright (Self)",
                    patient_age=28,
                    patient_gender="Male",
                    blood_group_id=bg_map.get('O+', 1),
                    quantity_units=1,
                    urgency="Normal",
                    required_date=date.today() + timedelta(days=5),
                    reason="Scheduled outpatient procedure requirement",
                    status="Pending",
                    requested_by=user_alex.name
                )
                db.add(user_req)

                hosp_req = BloodRequest(
                    request_code="REQ-20241010-HOSP01",
                    requester_type="Hospital",
                    hospital_id=primary_hosp_id,
                    patient_name="Metro General Trauma Emergency Ward",
                    patient_age=45,
                    patient_gender="Other",
                    blood_group_id=bg_map.get('A+', 2),
                    quantity_units=3,
                    urgency="Urgent",
                    required_date=date.today() + timedelta(days=1),
                    reason="Emergency batch supply for ICU surgery wing",
                    status="Approved",
                    requested_by="Metro General Hospital Coordinator"
                )
                db.add(hosp_req)

            # 8. Notifications
            if db.query(Notification).count() == 0:
                sample_notifs = [
                    ("⚠️ Central Low Stock Alert: AB-", "Stock for AB- is critically low (2 units remaining, threshold: 5).", "low_stock"),
                    ("⚠️ Central Low Stock Alert: B-", "Stock for B- is critically low (3 units remaining, threshold: 5).", "low_stock"),
                    ("🚨 New User Blood Request: O+ (1 Unit)", "Alexander Wright created a blood request for scheduled procedure.", "request_alert"),
                    ("🏥 Hospital Blood Request: A+ (3 Units)", "Metro City General Hospital requested 3 units for Trauma ICU.", "request_alert"),
                    ("🩸 Donation Received: O+ (+1 Unit)", "Received 1 unit (450 ml) from Alexander Wright. Central inventory updated.", "donation")
                ]
                for title, msg, n_type in sample_notifs:
                    db.add(Notification(title=title, message=msg, type=n_type, is_read=False))

            db.commit()
            return {'success': True, 'message': 'Neon PostgreSQL database seeded successfully with 4-role architecture!'}, 200
