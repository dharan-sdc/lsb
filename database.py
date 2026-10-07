import os
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from config import Config
from models import Base

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
    poolclass=NullPool if os.getenv("VERCEL") else None,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def test_db_connection():
    """Verify active database connection and log connection health."""
    start_time = time.time()
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT version();")).fetchone()
            latency_ms = (time.time() - start_time) * 1000
            db_version = res[0] if res else "PostgreSQL"
            print("=================================================================")
            print("🔌 [DATABASE CONNECTED] Successfully connected to Neon PostgreSQL!")
            print(f"📊 [DATABASE LATENCY] {latency_ms:.2f} ms")
            print(f"📦 [DATABASE ENGINE] {db_version.split(',')[0]}")
            print("=================================================================")
            return True, latency_ms
    except Exception as e:
        print("=================================================================")
        print(f"❌ [DATABASE ERROR] Connection failed: {e}")
        print("=================================================================")
        return False, 0

def init_db():
    print("🔄 [DATABASE INIT] Checking database connection...")
    success, _ = test_db_connection()
    if success:
        print("🛠️ [DATABASE SCHEMA] Ensuring all table schemas are created...")
        Base.metadata.create_all(bind=engine)
        
        # Safe column migrations for schema updates
        with engine.connect() as conn:
            migration_statements = [
                # Users table columns
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS blood_group_id INTEGER REFERENCES blood_groups(id);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS hospital_id INTEGER REFERENCES hospitals(id);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS age INTEGER;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(20);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS city VARCHAR(100);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(100);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS dob VARCHAR(30);",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_blood_group_verified BOOLEAN DEFAULT FALSE;",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_donor BOOLEAN DEFAULT FALSE;",
                
                # Hospitals table columns
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS city VARCHAR(100) DEFAULT 'Metropolis';",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS state VARCHAR(100) DEFAULT 'State';",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS website VARCHAR(150);",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS operating_hours VARCHAR(100) DEFAULT '24/7 Emergency Care';",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS emergency_contact VARCHAR(100);",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'Verified';",
                "ALTER TABLE hospitals ADD COLUMN IF NOT EXISTS has_inventory BOOLEAN DEFAULT TRUE;",

                # Patients table columns
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS department VARCHAR(100) DEFAULT 'General Ward';",
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS doctor_name VARCHAR(150);",
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS admission_notes TEXT;",

                # Donations table columns
                "ALTER TABLE blood_donations ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);",
                "ALTER TABLE blood_donations ADD COLUMN IF NOT EXISTS donor_name VARCHAR(150);",
                "ALTER TABLE blood_donations ALTER COLUMN donor_id DROP NOT NULL;",
                
                # Requests table columns
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS requester_type VARCHAR(30) DEFAULT 'User';",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS patient_name VARCHAR(150);",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS patient_age INTEGER;",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS patient_gender VARCHAR(20);",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS component_type VARCHAR(50) DEFAULT 'Whole Blood';",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS doctor_name VARCHAR(150);",
                "ALTER TABLE blood_requests ADD COLUMN IF NOT EXISTS department VARCHAR(100);",
                "ALTER TABLE blood_requests ALTER COLUMN patient_id DROP NOT NULL;"
            ]
            for stmt in migration_statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception as e:
                    print(f"Migration note: {e}")

        print("✅ [DATABASE SCHEMA] All database tables ready.")
        
        # Ensure standard blood groups, inventory, camps, units, and profile exist
        try:
            from models import BloodGroup, User
            from auth_utils import hash_password
            with SessionLocal() as db:
                # 1. Standard 8 Blood Groups Reference Matrix ONLY
                blood_groups_data = [
                    ('A+', 'Positive', 'A positive', 'A+, AB+', 'A+, A-, O+, O-'),
                    ('A-', 'Negative', 'A negative', 'A+, A-, AB+, AB-', 'A-, O-'),
                    ('B+', 'Positive', 'B positive', 'B+, AB+', 'B+, B-, O+, O-'),
                    ('B-', 'Negative', 'B negative', 'B+, B-, AB+, AB-', 'B-, O-'),
                    ('AB+', 'Positive', 'AB positive (Universal Receiver)', 'AB+', 'All Blood Groups'),
                    ('AB-', 'Negative', 'AB negative', 'AB+, AB-', 'AB-, A-, B-, O-'),
                    ('O+', 'Positive', 'O positive', 'O+, A+, B+, AB+', 'O+, O-'),
                    ('O-', 'Negative', 'O negative (Universal Donor)', 'All Blood Groups', 'O- only')
                ]
                for g_name, rh, desc, donate, receive in blood_groups_data:
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
                db.commit()

                # 2. Core System User Accounts (Created only if user table is empty / missing)
                users_data = [
                    ('System Administrator', 'admin@bloodbank.com', 'Admin@123', 'Admin', '+1-555-0100'),
                    
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
                db.commit()

                print("🩸 [DATABASE INIT] Reference data verified (8 Blood Groups & Core login accounts only).")
        except Exception as seed_err:
            print(f"⚠️ [DATABASE INIT NOTE] {seed_err}")

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

