"""
Setup script for CipherCare authentication system
Run this to initialize the database and create initial users
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    print("=" * 60)
    print("CipherCare Authentication System Setup")
    print("=" * 60)
    
    try:
        # Step 1: Initialize database
        print("\n📦 Step 1: Initializing PostgreSQL database...")
        from backend.database import setup_database
        
        if not setup_database():
            print("❌ Database setup failed!")
            return False
        
        print("✅ Database setup completed successfully")
        
        # Step 2: Verify environment variables
        print("\n🔍 Step 2: Verifying environment variables...")
        
        required_vars = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "BREVO_API_KEY"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
            print("   Update your .env file with these values")
        else:
            print("✅ All required environment variables are set")
        
        # Step 3: Test database connection
        print("\n🔌 Step 3: Testing database connection...")
        from backend.database import init_db_pool, get_db_connection
        
        if init_db_pool():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users")
                    user_count = cur.fetchone()[0]
                    print(f"✅ Database connected - {user_count} users found")
        else:
            print("❌ Database connection failed!")
            return False
        
        # Step 4: Test email service
        print("\n📧 Step 4: Testing email service...")
        from backend.email_service import email_service
        
        if email_service.enabled:
            print("✅ Brevo email service is configured")
        else:
            print("⚠️  Brevo API key not set - email features disabled")
        
        # Success!
        print("\n" + "=" * 60)
        print("✅ Setup completed successfully!")
        print("=" * 60)
        print("\n📝 Next steps:")
        print("1. Update .env with your Brevo API key if not done")
        print("2. Generate strong JWT_SECRET_KEY: openssl rand -hex 32")
        print("3. Start backend: python backend/main.py")
        print("4. Start frontend: cd frontend && npm run dev")
        print("5. Access login page: http://localhost:3000/auth/login")
        print("\n🔐 Default credentials:")
        print("   Username: attending | Password: password123")
        print("   Username: resident  | Password: password123")
        print("\n⚠️  Change these passwords in production!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
