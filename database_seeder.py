from datetime import datetime, timezone, date, timedelta
from database import get_db, init_db, engine
from models import Base, User, BloodGroup, Hospital, Donor, Patient, BloodInventory, BloodDonation, BloodRequest, BloodIssue, Notification, AuditLog
from auth_utils import hash_password

class DatabaseSeeder:
    @staticmethod
    def seed_database():
        init_db()
        with get_db() as db:
            # 1. Standard Blood Groups
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

            # 2. System Users (Admin, Staff, Doctor)
            users_data = [
                ('System Administrator', 'admin@bloodbank.com', 'Admin@123', 'Admin', '+1-555-0100'),
                ('Clinical Staff Member', 'staff@bloodbank.com', 'Staff@123', 'Staff', '+1-555-0101'),
                ('Dr. Robert Sterling', 'doctor@bloodbank.com', 'Doctor@123', 'Doctor', '+1-555-0103')
            ]

            for name, email, pwd, role, phone in users_data:
                u = db.query(User).filter(User.email == email).first()
                if not u:
                    u = User(
                        name=name,
                        email=email,
                        password_hash=hash_password(pwd),
                        role=role,
                        status='Active',
                        phone=phone
                    )
                    db.add(u)

            # 3. Hospitals
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

            # 4. Donors
            bg_map = {bg.group_name: bg.id for bg in db.query(BloodGroup).all()}
            donors_data = [
                ('Alexander Wright', 28, 'Male', 'O+', '+1-555-1101', 'alex.wright@email.com', '12 Oak Lane, Metro City', 'Fit & Healthy, no medications', date.today() - timedelta(days=95), 3, 'Eligible'),
                ('Sophia Martinez', 34, 'Female', 'A+', '+1-555-1102', 'sophia.m@email.com', '45 Pine St, Metro City', 'Hb: 13.8, regular donor', date.today() - timedelta(days=120), 5, 'Eligible'),
                ('David Kim', 22, 'Male', 'B+', '+1-555-1103', 'david.kim@email.com', '88 Maple Ave, Metro City', 'First time donor', date.today() - timedelta(days=40), 1, 'Eligible'),
                ('Emily Watson', 45, 'Female', 'O-', '+1-555-1104', 'emily.w@email.com', '101 Cedar Blvd, Metro City', 'Universal donor volunteer', date.today() - timedelta(days=150), 8, 'Eligible'),
                ('Lucas Silva', 19, 'Male', 'AB+', '+1-555-1105', 'lucas.s@email.com', '32 Elm Street, Metro City', 'Healthy young donor', date.today() - timedelta(days=200), 2, 'Eligible'),
                ('Hannah Brown', 17, 'Female', 'A-', '+1-555-1106', 'hannah.b@email.com', '57 Birch Road, Metro City', 'Under age threshold', None, 0, 'Ineligible'),
                ('Marcus Vance', 52, 'Male', 'B-', '+1-555-1107', 'marcus.v@email.com', '99 Walnut Dr, Metro City', 'Recent travel abroad', date.today() - timedelta(days=300), 4, 'Deferred'),
                ('Olivia Chen', 29, 'Female', 'AB-', '+1-555-1108', 'olivia.c@email.com', '140 Willow St, Metro City', 'Rare AB- donor volunteer', date.today() - timedelta(days=110), 3, 'Eligible')
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

            # 5. Patients
            hosp_map = {h.name: h.id for h in db.query(Hospital).all()}
            patients_data = [
                ('James Peterson', 42, 'Male', 'O+', 'Metro City General Hospital', 'Major Cardiovascular Surgery', '+1-555-2101', '77 Sunset Rd', 'Admitted'),
                ('Claire Beauchamp', 31, 'Female', 'A+', 'Apex Trauma & Emergency Care', 'Emergency Trauma Post-Accident', '+1-555-2102', '120 Horizon Way', 'Admitted'),
                ('Ethan Rodriguez', 12, 'Male', 'B+', 'St. Jude Children & Research Hospital', 'Thalassemia Major Transfusion', '+1-555-2103', '34 Beacon Hill', 'Admitted'),
                ('Grace Hopper', 68, 'Female', 'O-', 'Metro City General Hospital', 'Hip Replacement & Orthopedic Care', '+1-555-2104', '89 Pioneer Way', 'Admitted'),
                ('Liam Gallagher', 55, 'Male', 'AB-', 'Apex Trauma & Emergency Care', 'Acute Internal Hemorrhage', '+1-555-2105', '202 Central Ave', 'Admitted')
            ]

            for name, age, gender, bg_code, hosp_name, cond, contact, addr, status in patients_data:
                p = db.query(Patient).filter(Patient.name == name).first()
                if not p and bg_code in bg_map:
                    p = Patient(
                        name=name,
                        age=age,
                        gender=gender,
                        blood_group_id=bg_map[bg_code],
                        hospital_id=hosp_map.get(hosp_name),
                        condition=cond,
                        contact=contact,
                        address=addr,
                        status=status
                    )
                    db.add(p)

            db.flush()

            # 6. Notifications
            sample_notifs = [
                ("⚠️ Low Stock Alert: AB-", "Stock for AB- is critically low (2 units remaining, threshold: 5).", "low_stock"),
                ("⚠️ Low Stock Alert: B-", "Stock for B- is critically low (3 units remaining, threshold: 5).", "low_stock"),
                ("🚨 New Blood Request: O+ (2 Units)", "Urgent blood request raised for James Peterson at Metro City General Hospital.", "request_alert"),
                ("🩸 Donation Received: O+ (+1 Unit)", "Received 1 unit (450 ml) from Alexander Wright. Inventory updated.", "donation")
            ]

            if db.query(Notification).count() == 0:
                for title, msg, n_type in sample_notifs:
                    db.add(Notification(title=title, message=msg, type=n_type, is_read=False))

            db.commit()

            return {'success': True, 'message': 'Neon PostgreSQL database seeded successfully!'}, 200
