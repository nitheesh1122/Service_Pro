@echo off
echo 🔧 Running ServicePro Database Migration...
echo.

cd /d %~dp0

REM Check if database exists
if not exist "instance\servicepro.db" (
    echo ❌ Database not found at instance/servicepro.db
    echo Please run the Flask application first to create the database.
    pause
    exit /b 1
)

REM Run SQLite commands to add missing columns
sqlite3 instance/servicepro.db "ALTER TABLE service_provider ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending';"

sqlite3 instance/servicepro.db "CREATE TABLE IF NOT EXISTS verification_document (id INTEGER PRIMARY KEY AUTOINCREMENT, provider_id INTEGER NOT NULL, document_type VARCHAR(50) NOT NULL, file_path VARCHAR(255) NOT NULL, uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP, admin_notes TEXT, status VARCHAR(20) DEFAULT 'pending', FOREIGN KEY (provider_id) REFERENCES service_provider(id) ON DELETE CASCADE);"

sqlite3 instance/servicepro.db "CREATE INDEX IF NOT EXISTS idx_provider_verification_status ON service_provider(verification_status);"

sqlite3 instance/servicepro.db "UPDATE service_provider SET verification_status = 'verified' WHERE status = 'approved';"

echo.
echo ✅ Migration completed successfully!
echo.
echo 📊 Verification Status Summary:
sqlite3 instance/servicepro.db "SELECT COUNT(*) as verified FROM service_provider WHERE verification_status = 'verified';" "SELECT COUNT(*) as pending FROM service_provider WHERE verification_status = 'pending';"
echo.
echo You can now run your Flask application.
echo.
pause
