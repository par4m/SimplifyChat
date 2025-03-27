-- Create the database if it doesn't exist
CREATE DATABASE simplifychat;

-- Connect to the database
\c simplifychat;

-- Create the extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges to the simplifychat user
GRANT ALL PRIVILEGES ON DATABASE simplifychat TO simplifychat;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO simplifychat;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO simplifychat; 