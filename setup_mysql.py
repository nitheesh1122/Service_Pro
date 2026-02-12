#!/usr/bin/env python3
"""
ServicePro MySQL Database Setup Script
This script will create the database and insert proper data with correct password hashes
"""

import mysql.connector
from werkzeug.security import generate_password_hash
import sys
import os

def get_db_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',  # Change this to your MySQL username
            password='',  # Change this to your MySQL password
            charset='utf8mb4'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return None

def create_database_and_tables(connection):
    """Create database and tables"""
    cursor = connection.cursor()
    
    try:
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS servicepro_db")
        cursor.execute("USE servicepro_db")
        print("✅ Database 'servicepro_db' created/selected")
        
        # Create tables
        tables = {
            'user': """
                CREATE TABLE IF NOT EXISTS user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password VARCHAR(200) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    address TEXT,
                    pincode VARCHAR(10),
                    phone VARCHAR(15),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """,
            'service_provider': """
                CREATE TABLE IF NOT EXISTS service_provider (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    service_categories TEXT,
                    service_pincodes TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    availability TEXT,
                    hourly_rate FLOAT DEFAULT 0.0,
                    description TEXT,
                    experience_years INT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                )
            """,
            'service': """
                CREATE TABLE IF NOT EXISTS service (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(50) NOT NULL,
                    description TEXT,
                    base_price FLOAT DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """,
            'booking': """
                CREATE TABLE IF NOT EXISTS booking (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    provider_id INT NOT NULL,
                    service_id INT NOT NULL,
                    booking_date DATETIME NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    address TEXT NOT NULL,
                    total_amount FLOAT DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (provider_id) REFERENCES service_provider(id) ON DELETE CASCADE,
                    FOREIGN KEY (service_id) REFERENCES service(id) ON DELETE CASCADE
                )
            """,
            'review': """
                CREATE TABLE IF NOT EXISTS review (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    booking_id INT NOT NULL,
                    user_id INT NOT NULL,
                    provider_id INT NOT NULL,
                    rating INT NOT NULL,
                    comments TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (booking_id) REFERENCES booking(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (provider_id) REFERENCES service_provider(id) ON DELETE CASCADE
                )
            """,
            'message': """
                CREATE TABLE IF NOT EXISTS message (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sender_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (sender_id) REFERENCES user(id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES user(id) ON DELETE CASCADE
                )
            """
        }
        
        for table_name, table_sql in tables.items():
            cursor.execute(table_sql)
            print(f"✅ Table '{table_name}' created")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating tables: {e}")
        return False
    finally:
        cursor.close()

def insert_sample_data(connection):
    """Insert sample data with proper password hashes"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("USE servicepro_db")
        
        # Generate password hash for admin123
        admin_password = generate_password_hash('admin123')
        user_password = generate_password_hash('user123')
        
        # Insert services
        services = [
            ('Plumber', 'Professional plumbing services including repairs, installations, and maintenance', 500.00),
            ('Electrician', 'Electrical work including wiring, repairs, and installations', 400.00),
            ('Cleaner', 'Comprehensive cleaning services for homes and offices', 300.00),
            ('Carpenter', 'Skilled carpentry work for furniture and home improvements', 450.00),
            ('Painter', 'Professional painting services for interior and exterior projects', 350.00),
            ('AC Repair', 'Air conditioning repair and maintenance services', 600.00),
            ('Gardener', 'Landscaping and gardening services', 250.00),
            ('Appliance Repair', 'Home appliance repair and maintenance', 400.00)
        ]
        
        cursor.executemany(
            "INSERT INTO service (category, description, base_price) VALUES (%s, %s, %s)",
            services
        )
        print(f"✅ Inserted {len(services)} services")
        
        # Insert users
        users = [
            ('Admin User', 'admin@servicepro.com', admin_password, 'admin', '+1-555-0123', '123 Admin Street, Admin City', '12345'),
            ('John Smith', 'john@example.com', user_password, 'user', '+1-555-0124', '456 User Street, User City', '12346'),
            ('Sarah Johnson', 'sarah@example.com', user_password, 'user', '+1-555-0125', '789 Customer Ave, Customer City', '12347'),
            ('Mike Wilson', 'mike@example.com', user_password, 'provider', '+1-555-0126', '321 Provider Lane, Provider City', '12348'),
            ('Lisa Brown', 'lisa@example.com', user_password, 'provider', '+1-555-0127', '654 Service Road, Service City', '12349')
        ]
        
        cursor.executemany(
            "INSERT INTO user (name, email, password, role, phone, address, pincode) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            users
        )
        print(f"✅ Inserted {len(users)} users")
        
        # Insert service providers
        providers = [
            (4, '["Plumber", "Electrician"]', '12348,12349,12350', 'approved', 75.00, 'Experienced plumber and electrician with 10+ years of experience', 10),
            (5, '["Cleaner", "Painter"]', '12349,12350,12351', 'approved', 50.00, 'Professional cleaning and painting services', 8)
        ]
        
        cursor.executemany(
            "INSERT INTO service_provider (user_id, service_categories, service_pincodes, status, hourly_rate, description, experience_years) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            providers
        )
        print(f"✅ Inserted {len(providers)} service providers")
        
        # Insert sample bookings
        bookings = [
            (2, 1, 1, '2024-01-15 10:00:00', 'completed', '456 User Street, User City', 500.00),
            (3, 2, 4, '2024-01-20 14:00:00', 'in_progress', '789 Customer Ave, Customer City', 450.00)
        ]
        
        cursor.executemany(
            "INSERT INTO booking (user_id, provider_id, service_id, booking_date, status, address, total_amount) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            bookings
        )
        print(f"✅ Inserted {len(bookings)} bookings")
        
        # Insert sample reviews
        reviews = [
            (1, 2, 1, 5, 'Excellent service! Very professional and completed the work quickly.')
        ]
        
        cursor.executemany(
            "INSERT INTO review (booking_id, user_id, provider_id, rating, comments) VALUES (%s, %s, %s, %s, %s)",
            reviews
        )
        print(f"✅ Inserted {len(reviews)} reviews")
        
        # Insert sample messages
        messages = [
            (2, 4, 'Hi, I need help with a plumbing issue. When are you available?', 1),
            (4, 2, 'Hello! I can help you with that. I am available tomorrow morning.', 0)
        ]
        
        cursor.executemany(
            "INSERT INTO message (sender_id, receiver_id, message, is_read) VALUES (%s, %s, %s, %s)",
            messages
        )
        print(f"✅ Inserted {len(messages)} messages")
        
        # Create indexes
        indexes = [
            "CREATE INDEX idx_user_email ON user(email)",
            "CREATE INDEX idx_user_role ON user(role)",
            "CREATE INDEX idx_provider_status ON service_provider(status)",
            "CREATE INDEX idx_booking_user ON booking(user_id)",
            "CREATE INDEX idx_booking_provider ON booking(provider_id)",
            "CREATE INDEX idx_booking_status ON booking(status)",
            "CREATE INDEX idx_message_sender ON message(sender_id)",
            "CREATE INDEX idx_message_receiver ON message(receiver_id)",
            "CREATE INDEX idx_message_timestamp ON message(timestamp)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except mysql.connector.Error:
                pass  # Index might already exist
        
        print("✅ Created database indexes")
        
        connection.commit()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error inserting data: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def verify_data(connection):
    """Verify that data was inserted correctly"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("USE servicepro_db")
        
        # Check users
        cursor.execute("SELECT COUNT(*) FROM user")
        user_count = cursor.fetchone()[0]
        print(f"📊 Users in database: {user_count}")
        
        # Check services
        cursor.execute("SELECT COUNT(*) FROM service")
        service_count = cursor.fetchone()[0]
        print(f"📊 Services in database: {service_count}")
        
        # Check service providers
        cursor.execute("SELECT COUNT(*) FROM service_provider")
        provider_count = cursor.fetchone()[0]
        print(f"📊 Service providers in database: {provider_count}")
        
        # Show admin user
        cursor.execute("SELECT name, email, role FROM user WHERE role = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"👤 Admin user: {admin_user[0]} ({admin_user[1]})")
        
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ Error verifying data: {e}")
        return False
    finally:
        cursor.close()

def main():
    """Main setup function"""
    print("🏠 ServicePro MySQL Database Setup")
    print("=" * 50)
    
    # Get database connection
    connection = get_db_connection()
    if not connection:
        print("❌ Failed to connect to MySQL. Please check your credentials.")
        print("💡 Make sure MySQL is running and update the connection details in this script.")
        sys.exit(1)
    
    try:
        # Create database and tables
        if not create_database_and_tables(connection):
            sys.exit(1)
        
        # Insert sample data
        if not insert_sample_data(connection):
            sys.exit(1)
        
        # Verify data
        if not verify_data(connection):
            sys.exit(1)
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Login Credentials:")
        print("👤 Admin: admin@servicepro.com / admin123")
        print("👤 User: john@example.com / user123")
        print("👤 Provider: mike@example.com / user123")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        connection.close()

if __name__ == '__main__':
    main()
