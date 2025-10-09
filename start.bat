@echo off
echo 🏠 ServicePro - Starting Application...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
)

REM Run the application
echo 🚀 Starting ServicePro...
echo 📱 Application will be available at: http://localhost:5000
echo 👤 Admin login: admin@servicepro.com / admin123
echo ⏹️  Press Ctrl+C to stop the server
echo.
python run.py

pause 