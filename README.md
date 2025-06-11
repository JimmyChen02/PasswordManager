# PostgreSQL Password Manager

A secure multi-user password manager that uses PostgreSQL for data storage and strong encryption to protect your passwords.

## Features

- **Multi-user support**: Each user has their own encrypted password vault
- **Strong encryption**: Uses Fernet symmetric encryption with PBKDF2 key derivation
- **High security**: 1.2 million iterations for PBKDF2 to resist brute force attacks
- **PostgreSQL backend**: Reliable database storage with proper schema design
- **SSL connections**: Secure database connections required
- **User isolation**: Each user's data is completely separate and encrypted with their unique key

## Security Architecture

- **Master password**: Never stored, only used to derive encryption keys
- **Unique salts**: Each user gets a cryptographically random salt
- **Key derivation**: PBKDF2-HMAC-SHA256 with 1,200,000 iterations
- **Password hashing**: Username + master password combination hashed with SHA256
- **Encryption**: Fernet (AES 128 in CBC mode with HMAC-SHA256 authentication)

## Architecture Overview

This password manager runs on an **AWS EC2 instance** and connects to an **AWS RDS PostgreSQL database**. The application is accessed by SSH-ing into the EC2 instance and running the Python script directly.

## Prerequisites

Before you can run this application, you need:

- **SSH Key**: Your EC2 key pair file (`.pem`) 
- **AWS EC2 Instance**: Running with the application code
- **AWS RDS Instance**: PostgreSQL database accessible from EC2
- **Network Access**: Ability to connect to your EC2 instance
- Python 3.6+ (should be pre-installed on EC2 instance)
- Required Python packages (should be pre-installed on EC2 instance)

## Setup Instructions

### Step 1: Prepare Your SSH Key

Set proper permissions for your SSH key file:
```bash
chmod 400 your-key-file.pem
```

### Step 2: Connect to Your EC2 Instance

SSH into the EC2 instance where the application is installed:
```bash
ssh -i your-key-file.pem ec2-user@your-ec2-instance.compute-1.amazonaws.com
```

### Step 3: Configure Database Connection

Create a `.env` file on your EC2 instance with your RDS credentials:
```bash
nano .env
```

Add your database configuration:
```bash
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PORT=5432
DB_NAME=password_manager
DB_USER=your-db-user
DB_PASSWORD=your-db-password
```

### Step 4: Run the Password Manager

Start the application:
```bash
python3 password_manager.py
```

### Step 5: First Time Setup

When you first run the application:

1. **Enter a username** - This will be your account identifier
2. **Enter a master password** - This encrypts all your data (never stored anywhere)
3. **If the account doesn't exist**, you'll be prompted to create a new one
4. **Your master password** derives your unique encryption key

### Step 6: Using the Application

Once logged in, you can:
- **`view`**: Display all your stored passwords (decrypted)
- **`add`**: Add a new password entry
- **`q`**: Quit the application

## AWS Configuration Requirements

### EC2 Instance Setup

#### Security Group Configuration
Your EC2 security group must allow:
```
Type: SSH
Protocol: TCP
Port: 22
Source: Your IP address (recommended) or 0.0.0.0/0 for public access
```

#### Required Software
Ensure these are installed on your EC2 instance:
- Python 3.6+
- pip3
- psycopg2-binary
- cryptography
- python-dotenv
- boto3

### RDS Instance Setup

#### Instance Requirements
- **Engine**: PostgreSQL 12.x or higher
- **Instance Class**: t3.micro (minimum for development)
- **Storage**: 20GB minimum
- **Multi-AZ**: Recommended for production
- **Backup retention**: 7 days minimum

#### Security Group Configuration
Your RDS security group must allow:
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: Your EC2 security group ID
```

#### Database Setup
The application **automatically creates** all required tables, indexes, and database structures on first run. No manual setup is required.

Requirements:
1. **RDS Instance is running** and accessible
2. **Security groups** allow connections from your EC2 instance
3. **Database credentials** are correctly configured in environment variables
4. **SSL connections** are properly configured (required by default)

## Troubleshooting

### Common Issues and Solutions

#### SSH Connection Problems
- **Permission denied**: Ensure key file has correct permissions (`chmod 400 your-key-file.pem`)
- **Connection timeout**: Check security groups allow SSH access from your IP
- **Host key verification failed**: Add EC2 instance to known_hosts or use `-o StrictHostKeyChecking=no`
- **Key not found**: Verify the key file path is correct

Test your SSH connection:
```bash
ssh -i your-key-file.pem -o ConnectTimeout=10 ec2-user@your-ec2-instance.compute-1.amazonaws.com
```

#### Database Connection Problems
- Verify RDS instance is running and accessible from EC2
- Check VPC security groups allow PostgreSQL connections between EC2 and RDS
- Confirm database credentials in `.env` file are correct
- Test connectivity from EC2: `telnet your-rds-endpoint.region.rds.amazonaws.com 5432`

#### Application Problems
- **Python module not found**: Check if required packages are installed
- **Database tables not created**: Ensure RDS allows CREATE TABLE operations
- **Environment variables**: Verify `.env` file exists and contains correct credentials

Check Python dependencies:
```bash
python3 -c "import psycopg2, cryptography; print('Dependencies OK')"
```

Install missing dependencies if needed:
```bash
pip3 install psycopg2-binary cryptography python-dotenv boto3
```

#### Authentication Issues
- Master passwords are case-sensitive
- Username and master password combination must match exactly
- If you get "encryption errors," verify you're using the correct master password
  

## Database Administration (🚨ADMIN ACCESS ONLY‼️)

### Administrative Access

For database monitoring and maintenance, connect directly to your RDS instance:

```bash
psql -h your-rds-endpoint.region.rds.amazonaws.com -p 5432 -U your-db-admin -d password_manager
```

### Useful Administrative Queries

```sql
-- View all users (without sensitive data)
SELECT id, username, created_at FROM users ORDER BY created_at DESC;

-- Count passwords per user
SELECT 
    u.username,
    COUNT(sp.id) as password_count,
    u.created_at as user_created
FROM users u
LEFT JOIN stored_passwords sp ON u.id = sp.user_id
GROUP BY u.id, u.username, u.created_at
ORDER BY password_count DESC;

-- View password entries for a specific user (encrypted)
SELECT 
    sp.website,
    sp.username,
    sp.created_at,
    sp.updated_at
FROM stored_passwords sp
JOIN users u ON sp.user_id = u.id
WHERE u.username = 'your-username'
ORDER BY sp.website;

-- Get all user data with encrypted passwords (for charts/analysis)
SELECT 
    u.id as user_id, 
    u.username as username, 
    sp.website, 
    sp.username as account_username, 
    sp.encrypted_password 
FROM users u 
JOIN stored_passwords sp ON u.id = sp.user_id 
ORDER BY u.id;

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables
WHERE schemaname = 'public';
```

### Backup and Restore

```bash
# Create backup
pg_dump -h your-rds-endpoint.region.rds.amazonaws.com -p 5432 -U your-db-admin -d password_manager > backup.sql

# Restore from backup
psql -h your-rds-endpoint.region.rds.amazonaws.com -p 5432 -U your-db-admin -d password_manager < backup.sql
```

## Database Schema Reference

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    password_hash VARCHAR(64) NOT NULL,  -- SHA256 hash of username:master_password
    salt VARCHAR(255) NOT NULL,          -- Base64 encoded random salt
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(username, password_hash)
);
```

### Stored Passwords Table
```sql
CREATE TABLE stored_passwords (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    website VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    encrypted_password TEXT NOT NULL,    -- Fernet encrypted password
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Important Security Notes

⚠️ **Critical Security Information**

- **Master password**: This is never stored anywhere. If you forget it, your data cannot be recovered
- **Backup**: Consider backing up your database, but remember that without the master password, encrypted data is useless
- **Network security**: Ensure your database connection is secure (SSL/TLS)
- **Environment variables**: Keep your `.env` file secure and never commit it to version control
- **SSH Keys**: Never commit your `.pem` key files to version control
- **Database credentials**: Use strong passwords and limit access

## Advanced Configuration

### RDS Parameter Group (Optional)
For better performance, consider custom parameter group settings:
```
shared_preload_libraries = 'pg_stat_statements'
log_statement = 'all'
log_min_duration_statement = 1000
```

### EC2 Instance Management
```bash
# Check if application files are up to date
ls -la /home/ec2-user/

# View system logs
sudo journalctl -u ssh

# Check Python environment
python3 --version
pip3 list | grep -E "(psycopg2|cryptography|python-dotenv)"
```

## Development History

This password manager has evolved through multiple versions:
- **V1**: Single-user with file-based salt storage
- **V2**: Multi-user with JSON file storage
- **V3**: Current PostgreSQL-based multi-user system

The current version provides better security, scalability, and reliability compared to previous file-based approaches.

## Disclaimer

This software is provided as-is. While it implements industry-standard security practices, use it at your own risk. Always maintain proper backups and follow security best practices.
