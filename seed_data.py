import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database_seeder import DatabaseSeeder

if __name__ == '__main__':
    print("🌱 Seeding Neon PostgreSQL database with initial data...")
    res, code = DatabaseSeeder.seed_database()
    print(f"Result [{code}]: {res['message']}")

