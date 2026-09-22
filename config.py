import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://neondb_owner:npg_tl4oCQJjz3VM@ep-weathered-pond-b3yoeyc2-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20
    }
    
    SECRET_KEY = os.getenv("SECRET_KEY", "bloodbank_secret_key_2026_super_secure")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_token_bloodbank_2026")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    DEFAULT_LOW_STOCK_THRESHOLD = int(os.getenv("DEFAULT_LOW_STOCK_THRESHOLD", "5"))
    PORT = int(os.getenv("PORT", "5000"))
