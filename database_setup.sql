-- ServicePro Database Setup Script
-- Run this script in MySQL to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS servicepro_db;
USE servicepro_db;

-- Create users table
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
);

-- Create service_provider table
CREATE TABLE IF NOT EXISTS service_provider (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_categories TEXT,
    service_pincodes TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    verification_status VARCHAR(20) DEFAULT 'pending',
    availability TEXT,
    hourly_rate FLOAT DEFAULT 0.0,
    description TEXT,
    experience_years INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create service table
CREATE TABLE IF NOT EXISTS service (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    base_price FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create booking table
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
);

-- Create review table
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
);

-- Create message table
CREATE TABLE IF NOT EXISTS message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Create verification_document table
CREATE TABLE IF NOT EXISTS verification_document (
    id INT AUTO_INCREMENT PRIMARY KEY,
    provider_id INT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin_notes TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (provider_id) REFERENCES service_provider(id) ON DELETE CASCADE
);

-- Insert default services
INSERT INTO service (category, description, base_price) VALUES
('Plumber', 'Professional plumbing services including repairs, installations, and maintenance', 500.00),
('Electrician', 'Electrical work including wiring, repairs, and installations', 400.00),
('Cleaner', 'Comprehensive cleaning services for homes and offices', 300.00),
('Carpenter', 'Skilled carpentry work for furniture and home improvements', 450.00),
('Painter', 'Professional painting services for interior and exterior projects', 350.00);

-- Insert admin user (password: admin123)
INSERT INTO user (name, email, password, role) VALUES
('Admin', 'admin@servicepro.com', 'pbkdf2:sha256:600000$your-hash-here', 'admin');

-- Create indexes for better performance
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_role ON user(role);
CREATE INDEX idx_provider_status ON service_provider(status);
CREATE INDEX idx_provider_verification_status ON service_provider(verification_status);
CREATE INDEX idx_booking_user ON booking(user_id);
CREATE INDEX idx_booking_provider ON booking(provider_id);
CREATE INDEX idx_booking_status ON booking(status);
CREATE INDEX idx_message_sender ON message(sender_id);
CREATE INDEX idx_message_receiver ON message(receiver_id);
CREATE INDEX idx_message_timestamp ON message(timestamp);

-- Show tables
SHOW TABLES;

-- Show sample data
SELECT 'Users:' as info;
SELECT id, name, email, role FROM user LIMIT 5;

SELECT 'Services:' as info;
SELECT * FROM service;

SELECT 'Database setup completed successfully!' as status; 