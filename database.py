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
        print("✅ [DATABASE SCHEMA] All database tables ready.")

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

