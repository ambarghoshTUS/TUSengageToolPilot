-- TUS Engage Tool Pilot - Database Initialization Script
-- This script creates the initial database schema
-- PostgreSQL 16+ compatible

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- USER MANAGEMENT TABLES
-- ============================================

-- User roles enumeration
CREATE TYPE user_role AS ENUM ('executive', 'staff', 'public', 'admin');

-- Users table with authentication
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role NOT NULL DEFAULT 'public',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(user_id),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Index for faster lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================
-- DATA SUBMISSION TRACKING
-- ============================================

-- File upload status enumeration
CREATE TYPE upload_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'rejected');

-- Uploaded files tracking
CREATE TABLE IF NOT EXISTS uploaded_files (
    file_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    mime_type VARCHAR(100),
    upload_status upload_status DEFAULT 'pending',
    uploaded_by UUID REFERENCES users(user_id) ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    rows_processed INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    error_message TEXT,
    validation_notes TEXT,
    CONSTRAINT valid_file_size CHECK (file_size > 0)
);

-- Index for tracking uploads
CREATE INDEX idx_uploaded_files_status ON uploaded_files(upload_status);
CREATE INDEX idx_uploaded_files_user ON uploaded_files(uploaded_by);
CREATE INDEX idx_uploaded_files_date ON uploaded_files(uploaded_at);

-- ============================================
-- MAIN DATA STORAGE (Flexible Schema)
-- ============================================

-- Main engagement data table (flexible for changing headers)
-- This table uses JSONB for flexibility with changing data structures
CREATE TABLE IF NOT EXISTS engagement_data (
    data_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
    row_number INTEGER NOT NULL,
    
    -- Core fields (update these based on your template)
    submission_date DATE,
    department VARCHAR(255),
    category VARCHAR(255),
    
    -- Flexible JSONB storage for dynamic fields
    -- This allows for template changes without schema migrations
    data_fields JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT valid_data_fields CHECK (jsonb_typeof(data_fields) = 'object')
);

-- Indexes for better query performance
CREATE INDEX idx_engagement_data_file ON engagement_data(file_id);
CREATE INDEX idx_engagement_data_date ON engagement_data(submission_date);
CREATE INDEX idx_engagement_data_department ON engagement_data(department);
CREATE INDEX idx_engagement_data_category ON engagement_data(category);
CREATE INDEX idx_engagement_data_fields ON engagement_data USING GIN (data_fields);

-- ============================================
-- DATA VALIDATION RULES
-- ============================================

-- Store validation rules for file uploads
CREATE TABLE IF NOT EXISTS validation_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) UNIQUE NOT NULL,
    rule_description TEXT,
    field_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    validation_regex VARCHAR(500),
    min_value NUMERIC,
    max_value NUMERIC,
    allowed_values JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TEMPLATE MANAGEMENT
-- ============================================

-- Store template configurations
CREATE TABLE IF NOT EXISTS upload_templates (
    template_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name VARCHAR(255) UNIQUE NOT NULL,
    template_version VARCHAR(50) NOT NULL,
    description TEXT,
    headers JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(user_id)
);

-- Index for template lookups
CREATE INDEX idx_templates_active ON upload_templates(is_active);

-- ============================================
-- AUDIT LOGGING
-- ============================================

-- Comprehensive audit trail
CREATE TABLE IF NOT EXISTS audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for audit queries
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_date ON audit_log(created_at);
CREATE INDEX idx_audit_table ON audit_log(table_name);

-- ============================================
-- DASHBOARD VIEWS (Materialized for Performance)
-- ============================================

-- Executive Dashboard View (Detailed)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_executive_dashboard AS
SELECT 
    ed.data_id,
    ed.submission_date,
    ed.department,
    ed.category,
    ed.data_fields,
    uf.original_filename,
    uf.uploaded_at,
    u.full_name as uploaded_by_name,
    u.role as uploader_role
FROM engagement_data ed
LEFT JOIN uploaded_files uf ON ed.file_id = uf.file_id
LEFT JOIN users u ON uf.uploaded_by = u.user_id
WHERE ed.is_active = TRUE
AND uf.upload_status = 'completed';

-- Create indexes on materialized view
CREATE INDEX idx_mv_exec_date ON mv_executive_dashboard(submission_date);
CREATE INDEX idx_mv_exec_dept ON mv_executive_dashboard(department);

-- Staff Dashboard View (Medium Detail)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_staff_dashboard AS
SELECT 
    ed.data_id,
    ed.submission_date,
    ed.department,
    ed.category,
    ed.data_fields - 'sensitive_field' as data_fields, -- Remove sensitive fields
    uf.uploaded_at
FROM engagement_data ed
LEFT JOIN uploaded_files uf ON ed.file_id = uf.file_id
WHERE ed.is_active = TRUE
AND uf.upload_status = 'completed';

-- Create indexes on materialized view
CREATE INDEX idx_mv_staff_date ON mv_staff_dashboard(submission_date);
CREATE INDEX idx_mv_staff_dept ON mv_staff_dashboard(department);

-- Public Dashboard View (High-Level Summary)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_public_dashboard AS
SELECT 
    DATE_TRUNC('month', ed.submission_date) as month,
    ed.department,
    ed.category,
    COUNT(*) as total_submissions,
    COUNT(DISTINCT ed.file_id) as unique_uploads
FROM engagement_data ed
LEFT JOIN uploaded_files uf ON ed.file_id = uf.file_id
WHERE ed.is_active = TRUE
AND uf.upload_status = 'completed'
GROUP BY DATE_TRUNC('month', ed.submission_date), ed.department, ed.category;

-- Create indexes on materialized view
CREATE INDEX idx_mv_public_month ON mv_public_dashboard(month);
CREATE INDEX idx_mv_public_dept ON mv_public_dashboard(department);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_engagement_data_updated_at BEFORE UPDATE ON engagement_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON upload_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_all_dashboards()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_executive_dashboard;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_staff_dashboard;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_public_dashboard;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- INITIAL DATA SEEDING
-- ============================================

-- Create default admin user (password: AdminPass123! - CHANGE IMMEDIATELY)
-- Password hash generated using bcrypt
INSERT INTO users (username, email, password_hash, full_name, role, is_active)
VALUES (
    'admin',
    'admin@tus.ie',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIBL.5I3IW',
    'System Administrator',
    'admin',
    TRUE
) ON CONFLICT (username) DO NOTHING;

-- Insert default validation rules
INSERT INTO validation_rules (rule_name, rule_description, field_name, data_type, is_required)
VALUES 
    ('date_required', 'Submission date must be present', 'submission_date', 'date', TRUE),
    ('department_required', 'Department must be specified', 'department', 'string', TRUE)
ON CONFLICT (rule_name) DO NOTHING;

-- Grant necessary permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO tusadmin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO tusadmin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO tusadmin;
