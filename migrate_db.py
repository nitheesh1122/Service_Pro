#!/usr/bin/env python3
"""
Database Migration Script for Service Provider Verification
Run this script to add verification fields to existing SQLite database
"""

import sqlite3
import os
import sys

def run_migration():
    # Database path
    db_path = 'instance/servicepro.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please run the Flask application first to create the database.")
        return False

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("🔄 Starting database migration...")

        # Add verification_status column to service_provider table
        try:
            cursor.execute("ALTER TABLE service_provider ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending'")
            print("✓ Added verification_status column to service_provider table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("ℹ️  verification_status column already exists")
            else:
                raise e

        # Create verification_document table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS verification_document (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                document_type VARCHAR(50) NOT NULL,
                file_path VARCHAR(255) NOT NULL,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                admin_notes TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                FOREIGN KEY (provider_id) REFERENCES service_provider(id) ON DELETE CASCADE
            )
        ''')
        print("✓ Created verification_document table")

        # Add indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_provider_verification_status ON service_provider(verification_status)')
        print("✓ Added index for verification_status")

        # Update existing providers to have verified status if they were already approved
        cursor.execute("UPDATE service_provider SET verification_status = 'verified' WHERE status = 'approved'")
        updated_count = cursor.rowcount
        print(f"✓ Updated {updated_count} existing approved providers to verified status")

        # Commit changes
        conn.commit()

        # Show migration results
        cursor.execute("SELECT COUNT(*) FROM service_provider WHERE verification_status = 'verified'")
        verified_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM service_provider WHERE verification_status = 'pending'")
        pending_count = cursor.fetchone()[0]

        print("\n✅ Migration completed successfully!")
        print("📊 Verification Status Summary:")
        print(f"   • Verified providers: {verified_count}")
        print(f"   • Pending providers: {pending_count}")

        # Show table schema
        print("\n📋 Updated service_provider table schema:")
        cursor.execute("PRAGMA table_info(service_provider)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   • {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")

        return True

    except sqlite3.Error as e:
        print(f"❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
