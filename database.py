import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from config import Config
from models import Base

engine = create_engine(
    Config.SQLALCHEMY_DATABASE_URI,
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
                "ALTER TABLE blood_requests ALTER COLUMN patient_id DROP NOT NULL;"
            ]
            for stmt in migration_statements:
                try:
                    conn.execute(text(stmt))
                    conn.commit()
                except Exception as e:
                    print(f"Migration note: {e}")

        print("✅ [DATABASE SCHEMA] All database tables ready.")

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
