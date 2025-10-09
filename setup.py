#!/usr/bin/env python3
"""
ServicePro Setup Script
Automates the initial setup and configuration of the ServicePro application.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_banner():
    """Print the application banner."""
    print("=" * 60)
    print("🚀 ServicePro - Smart Household Service Management")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("📦 Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
            print("✅ Virtual environment created successfully!")
        except subprocess.CalledProcessError:
            print("❌ Failed to create virtual environment.")
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists.")

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        # Determine the pip command based on the OS
        if os.name == 'nt':  # Windows
            pip_cmd = "venv\\Scripts\\pip"
        else:  # Unix/Linux/macOS
            pip_cmd = "venv/bin/pip"
        
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.")
        sys.exit(1)

def create_env_file():
    """Create .env file with default configuration."""
    env_content = """# ServicePro Environment Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=mysql+pymysql://root:password@localhost/servicepro_db
FLASK_ENV=development
FLASK_DEBUG=True

# Email configuration (optional)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created successfully!")
    else:
        print("✅ .env file already exists.")

def create_directories():
    """Create necessary directories."""
    directories = ["uploads", "logs", "static"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created successfully!")

def setup_sqlite_database():
    """Set up SQLite database for development (alternative to MySQL)."""
    print("🗄️ Setting up SQLite database for development...")
    
    # Update the database URL to use SQLite
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r") as f:
            content = f.read()
        
        # Replace MySQL URL with SQLite
        content = content.replace(
            "DATABASE_URL=mysql+pymysql://root:password@localhost/servicepro_db",
            "DATABASE_URL=sqlite:///servicepro.db"
        )
        
        with open(env_file, "w") as f:
            f.write(content)
    
    print("✅ SQLite database configured!")

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Activate the virtual environment:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/macOS
        print("   source venv/bin/activate")
    
    print("\n2. Update the .env file with your database credentials")
    print("3. Run the application:")
    print("   python app.py")
    print("\n4. Open your browser and go to: http://localhost:5000")
    print("\n5. Login with admin credentials:")
    print("   Email: admin@servicepro.com")
    print("   Password: admin123")
    print("\n📚 For more information, see README.md")

def main():
    """Main setup function."""
    print_banner()
    
    print("🔍 Checking system requirements...")
    check_python_version()
    print()
    
    print("🚀 Starting setup process...")
    create_virtual_environment()
    print()
    
    install_dependencies()
    print()
    
    create_env_file()
    print()
    
    create_directories()
    print()
    
    setup_sqlite_database()
    print()
    
    print_next_steps()

if __name__ == "__main__":
    main() 