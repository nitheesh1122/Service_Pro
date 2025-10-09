@echo off
echo ========================================
echo ServicePro Database Analysis Report
echo ========================================
echo.

echo USERS TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT id, name, email, role, created_at FROM user ORDER BY created_at DESC;"
echo.

echo SERVICE PROVIDERS TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT sp.id, u.name as provider_name, u.email, sp.status, sp.hourly_rate, sp.experience_years FROM service_provider sp JOIN user u ON sp.user_id = u.id;"
echo.

echo SERVICES TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT id, category, description, base_price, is_active FROM service;"
echo.

echo BOOKINGS TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT b.id, u.name as customer, p.name as provider, s.category, b.status, b.total_amount, b.booking_date FROM booking b JOIN user u ON b.user_id = u.id JOIN service_provider sp ON b.provider_id = sp.id JOIN user p ON sp.user_id = p.id JOIN service s ON b.service_id = s.id ORDER BY b.created_at DESC;"
echo.

echo REVIEWS TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT r.id, u.name as customer, p.name as provider, r.rating, r.comments FROM review r JOIN user u ON r.user_id = u.id JOIN service_provider sp ON r.provider_id = sp.id JOIN user p ON sp.user_id = p.id;"
echo.

echo MESSAGES TABLE:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT m.id, s.name as sender, r.name as receiver, m.message, m.timestamp, m.is_read FROM message m JOIN user s ON m.sender_id = s.id JOIN user r ON m.receiver_id = r.id ORDER BY m.timestamp DESC;"
echo.

echo DATABASE STATISTICS:
echo ========================================
sqlite3 "d:/ServicePro/instance/servicepro.db" -header -column "SELECT 'Users' as table_name, COUNT(*) as count FROM user UNION ALL SELECT 'Providers', COUNT(*) FROM service_provider UNION ALL SELECT 'Services', COUNT(*) FROM service UNION ALL SELECT 'Bookings', COUNT(*) FROM booking UNION ALL SELECT 'Reviews', COUNT(*) FROM review UNION ALL SELECT 'Messages', COUNT(*) FROM message;"
echo.

echo ========================================
echo Report completed!
echo ========================================
pause
