-- ServicePro Database Migration Script
-- Run this script to add verification fields to existing databases

-- Add verification_status column to service_provider table
ALTER TABLE service_provider ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending';

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

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_provider_verification_status ON service_provider(verification_status);

-- Update existing providers to have verified status if they were already approved
UPDATE service_provider SET verification_status = 'verified' WHERE status = 'approved';

-- Show migration results
SELECT 'Migration completed successfully!' as status;

SELECT 'Service Providers:' as info;
SELECT id, user_id, status, verification_status FROM service_provider;

SELECT 'Verification Documents:' as info;
SELECT * FROM verification_document;
