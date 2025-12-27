#!/usr/bin/env python3
"""Add OTP columns to users table"""
import sys
from backend.database import get_db_connection, init_db_pool

def add_otp_columns():
    """Add OTP columns to users table if they don't exist"""
    try:
        init_db_pool()
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Add otp_code column
                try:
                    cur.execute("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS otp_code VARCHAR(6)
                    """)
                    print("✓ Added otp_code column")
                except Exception as e:
                    print(f"ℹ️  otp_code column: {e}")
                
                # Add otp_expires column
                try:
                    cur.execute("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS otp_expires TIMESTAMP
                    """)
                    print("✓ Added otp_expires column")
                except Exception as e:
                    print(f"ℹ️  otp_expires column: {e}")
                
                # Add otp_attempts column
                try:
                    cur.execute("""
                        ALTER TABLE users 
                        ADD COLUMN IF NOT EXISTS otp_attempts INTEGER DEFAULT 0
                    """)
                    print("✓ Added otp_attempts column")
                except Exception as e:
                    print(f"ℹ️  otp_attempts column: {e}")
                
                print("\n✓ Migration completed successfully!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 50)
    print("ADD OTP COLUMNS TO USERS TABLE")
    print("=" * 50)
    add_otp_columns()
