-- ServicePro Database Queries
-- Use these queries to check your database data

-- 1. View all users with their roles
SELECT 
    id,
    name,
    email,
    role,
    phone,
    pincode,
    created_at
FROM user
ORDER BY created_at DESC;

-- 2. View service providers with their details
SELECT 
    sp.id,
    u.name,
    u.email,
    u.phone,
    sp.service_categories,
    sp.service_pincodes,
    sp.status,
    sp.hourly_rate,
    sp.experience_years
FROM service_provider sp
JOIN user u ON sp.user_id = u.id
ORDER BY sp.id;

-- 3. View all services
SELECT 
    id,
    category,
    description,
    base_price,
    is_active
FROM service
ORDER BY category;

-- 4. View all bookings with details
SELECT 
    b.id,
    u.name as customer_name,
    p.user_id as provider_id,
    s.category as service_type,
    b.booking_date,
    b.status,
    b.total_amount,
    b.address,
    b.created_at
FROM booking b
JOIN user u ON b.user_id = u.id
JOIN service_provider sp ON b.provider_id = sp.id
JOIN user p ON sp.user_id = p.id
JOIN service s ON b.service_id = s.id
ORDER BY b.created_at DESC;

-- 5. View reviews and ratings
SELECT 
    r.id,
    u.name as reviewer_name,
    p.user_id as provider_id,
    r.rating,
    r.comments,
    r.created_at
FROM review r
JOIN user u ON r.user_id = u.id
JOIN service_provider sp ON r.provider_id = sp.id
JOIN user p ON sp.user_id = p.id
ORDER BY r.created_at DESC;

-- 6. View messages between users
SELECT 
    m.id,
    s.name as sender_name,
    r.name as receiver_name,
    m.message,
    m.timestamp,
    m.is_read
FROM message m
JOIN user s ON m.sender_id = s.id
JOIN user r ON m.receiver_id = r.id
ORDER BY m.timestamp DESC;

-- 7. Get booking statistics
SELECT 
    status,
    COUNT(*) as count
FROM booking
GROUP BY status;

-- 8. Get user statistics by role
SELECT 
    role,
    COUNT(*) as count
FROM user
GROUP BY role;

-- 9. Get provider statistics by status
SELECT 
    status,
    COUNT(*) as count
FROM service_provider
GROUP BY status;

-- 10. Get average rating for each provider
SELECT 
    u.name as provider_name,
    AVG(r.rating) as average_rating,
    COUNT(r.id) as total_reviews
FROM service_provider sp
JOIN user u ON sp.user_id = u.id
LEFT JOIN review r ON sp.id = r.provider_id
GROUP BY sp.id, u.name
ORDER BY average_rating DESC;
