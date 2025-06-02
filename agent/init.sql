-- Initial database setup for onboarding calls system
-- This script runs when PostgreSQL container first starts

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE onboarding_calls TO postgres;

-- Create basic indexes for performance
-- (Tables will be created by Alembic migrations)
