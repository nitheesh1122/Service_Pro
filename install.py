#!/usr/bin/env python3
"""
ServicePro - Installation Script
Run this script to set up the ServicePro application
"""

import os
import sys
import subprocess
import sqlite3

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_database():
    """Create SQLite database and tables"""
    print("🗄️  Setting up database...")
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
            
            # Create admin user if not exists
            from app import User, Service, generate_password_hash
            admin = User.query.filter_by(role='admin').first()
            if not admin:
                admin = User(
                    name='Admin',
                    email='admin@servicepro.com',
                    password=generate_password_hash('admin123'),
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created")
            
            # Create default services if not exists
            services = Service.query.all()
            if not services:
                default_services = [
                    Service(category='Plumber', description='Plumbing services', base_price=500),
                    Service(category='Electrician', description='Electrical services', base_price=400),
                    Service(category='Cleaner', description='Cleaning services', base_price=300),
                    Service(category='Carpenter', description='Carpentry services', base_price=450),
                    Service(category='Painter', description='Painting services', base_price=350)
                ]
                for service in default_services:
                    db.session.add(service)
                db.session.commit()
                print("✅ Default services created")
        
        print("✅ Database setup completed")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ['uploads', 'logs', 'instance']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️  Directory already exists: {directory}")

def main():
    """Main installation process"""
    print("🏠 ServicePro Installation")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Setup database
    if not create_database():
        sys.exit(1)
    
    print("\n🎉 Installation completed successfully!")
    print("\n📋 Next steps:")
    print("1. Run the application: python run.py")
    print("2. Open your browser: http://localhost:5000")
    print("3. Login as admin: admin@servicepro.com / admin123")
    print("\n🚀 Happy coding!")

if __name__ == '__main__':
    main() 