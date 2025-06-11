# PostgreSQL Password Manager - AWS Production Setup

![Python](https://img.shields.io/badge/python-3.6+-green.svg)
![PostgreSQL](https://img.shields.io/badge/postgresql-12+-blue.svg)
![Security](https://img.shields.io/badge/security-high-brightgreen.svg)
![AWS](https://img.shields.io/badge/deployment-AWS-orange.svg)
![Terminal](https://img.shields.io/badge/interface-terminal-black.svg)

A secure multi-user password manager that runs in the terminal and uses PostgreSQL for data storage and strong encryption to protect your passwords.

## Features

- **Terminal-based interface**: Simple command-line interaction for secure password management
- **Multi-user support**: Each user has their own encrypted password vault
- **Strong encryption**: Uses Fernet symmetric encryption with PBKDF2 key derivation
- **High security**: 1.2 million iterations for PBKDF2 to resist brute force attacks
- **PostgreSQL backend**: Reliable database storage with proper schema design
- **SSL connections**: Secure database connections required
- **User isolation**: Each user's data is completely separate and encrypted with their unique key
- **Cross-platform**: Works on Linux, macOS, and Windows terminals

## AWS Deployment

This password manager is designed to run on **AWS EC2** with **AWS RDS PostgreSQL** for production use. The RDS database is configured as **private** (not publicly accessible) for enhanced security.

### AWS Prerequisites

- **SSH Key**: Your EC2 key pair file (`.pem`) 
- **AWS EC2 Instance**: Running with the application code
- **AWS RDS Instance**: PostgreSQL database in private subnet (same VPC as EC2)
- **Network Access**: Ability to connect to your EC2 instance via SSH

### AWS Setup Instructions

#### Step 1: Prepare Your SSH Key

Set proper permissions for your SSH key file:
```bash
chmod 400 your-key-file.pem
```

#### Step 2: Connect to Your EC2 Instance

SSH into the EC2 instance where the application is installed:
```bash
ssh -i your-key-file.pem ec2-user@your-ec2-public-ip
```

#### Step 3: Install Dependencies on EC2

Once connected to your EC2 instance:
```bash
# Install Python dependencies
pip3 install psycopg2-binary cryptography python-dotenv

# Clone the repository (if not already done)
git clone https://github.com/JimmyChen02/PasswordManager.git
cd PasswordManager
```

#### Step 4: Configure Database Connection

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

#### Step 5: Run the Password Manager

Start the application in your EC2 terminal:
```bash
python3 password_manager.py
```
The application will run in the SSH terminal session.

### Using the Terminal Interface

The password manager runs entirely in your terminal. Here's what you'll see:

1. **Login prompt**: Enter your username and master password
2. **Main menu**: Choose from available commands
3. **Interactive prompts**: Follow the prompts to add or view passwords
4. **Secure display**: Passwords are displayed directly in the terminal (ensure privacy)

### First Time Setup

When you first run the application:

1. **Enter a username** - This will be your account identifier
2. **Enter a master password** - This encrypts all your data (never stored anywhere)
3. **If the account doesn't exist**, you'll be prompted to create a new one
4. **Your master password** derives your unique encryption key

### Commands

Once logged in, you can use these terminal commands:
- **`view`**: Display all your stored passwords (decrypted) in the terminal
- **`add`**: Add a new password entry through interactive prompts
- **`delete`**: Remove a password entry through interactive selection
- **`q`**: Quit the application and return to your shell

**Example terminal session:**
```
=== PostgreSQL Multi-User Password Manager ===
Database tables created successfully!
Enter your username: Jimmy
Enter your master password: 1234

No account found for username 'Jimmy' with the provided password.
Do you have an existing account? (yes/no): yes
Either your username or password is incorrect. Please try again with correct credentials.

Enter your username: Jimmy
Enter your master password: 123412

No account found for username 'Jimmy' with the provided password.
Do you have an existing account? (yes/no): yes
Either your username or password is incorrect. Please try again with correct credentials.

Enter your username: Jimmy
Enter your master password: GhostBin87@
Master password accepted - existing data verified.

Would you like to add a new password, view existing ones, or delete a password (view/add/delete), press q to quit? view

--- Your Stored Passwords ---
Website                        Username                       Password
------------------------------------------------------------------------------------------
Github                         JimmyChen02                    908Mafia$*!
Google                         jc3673@cornell.edu             GoBigRed228!?
Spotify                        Jimmy123User                   Data123!$%&()
--- End of Passwords ---

Would you like to add a new password, view existing ones, or delete a password (view/add/delete), press q to quit? delete

==== Your Stored Passwords ====
1. Github - JimmyChen02
2. Google - jc3673@cornell.edu
3. Spotify - Jimmy123User
Enter the number of the password to delete: 3
Are you sure you want to delete Spotify password? (yes/no): yes
Password for Spotify deleted successfully!

Would you like to add a new password, view existing ones, or delete a password (view/add/delete), press q to quit? view

--- Your Stored Passwords ---
Website                        Username                       Password
------------------------------------------------------------------------------------------
Github                         JimmyChen02                    908Mafia$*!
Google                         jc3673@cornell.edu             GoBigRed228!?
--- End of Passwords ---
```

## Security Architecture

- **Master password**: Never stored, only used to derive encryption keys
- **Unique salts**: Each user gets a cryptographically random salt
- **Key derivation**: PBKDF2-HMAC-SHA256 with 1,200,000 iterations
- **Password hashing**: Username + master password combination hashed with SHA256
- **Encryption**: Fernet (AES 128 in CBC mode with HMAC-SHA256 authentication)

### AWS Configuration Requirements

#### 📌 EC2 Instance Setup

**Security Group Configuration**
Your EC2 security group must allow:
```
Type: SSH
Protocol: TCP
Port: 22
Source: Your IP address (recommended) or 0.0.0.0/0 for public access
```

**Required Software**
Ensure these are installed on your EC2 instance:
- Python 3.6+
- pip3
- psycopg2-binary
- cryptography
- python-dotenv

#### 📌 RDS Instance Setup

**Instance Requirements**
- **Engine**: PostgreSQL 12.x or higher
- **Publicly Accessible**: **NO** (Private for security)
- **Instance Class**: t3.micro (minimum for development)
- **Storage**: 20GB minimum
- **Multi-AZ**: Recommended for production
- **Backup retention**: 7 days minimum

**Security Group Configuration**
Your RDS security group must allow:
```
Type: PostgreSQL
Protocol: TCP
Port: 5432
Source: Your EC2 security group ID (NOT 0.0.0.0/0)
```

**Database Setup**
The application **automatically creates** all required tables, indexes, and database structures on first run. No manual setup is required.

### Network Architecture

```
Internet → EC2 (Public Subnet) → RDS (Private Subnet)
                ↑                    ↑
        Your SSH Connection     Private Database
```

Requirements:
1. **EC2 and RDS instances** are in the **same VPC**
2. **RDS is in private subnet** (not publicly accessible)
3. **Security groups** allow connections from EC2 to RDS only
4. **EC2 has public IP** for SSH access
5. **Database credentials** are correctly configured in environment variables
6. **SSL connections** are properly configured (required by default)

### Why This Setup is Secure

- **Database isolation**: RDS is not accessible from the internet
- **Network segmentation**: Database is in private subnet
- **Access control**: Only your EC2 instance can reach the database
- **Encrypted connections**: All database connections use SSL/TLS
- **Limited exposure**: Only SSH port 22 is exposed to the internet

## Troubleshooting

### Common Issues and Solutions

#### SSH Connection Problems
- **Permission denied**: Ensure key file has correct permissions (`chmod 400 your-key-file.pem`)
- **Connection timeout**: Check security groups allow SSH access from your IP
- **Host key verification failed**: Add EC2 instance to known_hosts or use `-o StrictHostKeyChecking=no`
- **Key not found**: Verify the key file path is correct

Test your SSH connection:
```bash
ssh -i your-key-file.pem -o ConnectTimeout=10 ec2-user@your-ec2-public-ip
```

#### Database Connection Problems
- **Connection timeout**: Most likely cause is **RDS not publicly accessible** - this is expected and correct
- **Must run on EC2**: The application must be run from EC2, not from your local machine
- **Check VPC configuration**: Ensure EC2 and RDS are in the **same VPC**
- **Security group rules**: Verify RDS security group allows connections from EC2 security group
- **Database status**: Confirm RDS instance is in "Available" status

#### Application Problems
- **Python module not found**: Check if required packages are installed on EC2
- **Database tables not created**: Ensure database allows CREATE TABLE operations
- **Environment variables**: Verify `.env` file exists on EC2 and contains correct credentials

Check Python dependencies on EC2:
```bash
python3 -c "import psycopg2, cryptography; print('Dependencies OK')"
```

Install missing dependencies if needed:
```bash
pip3 install psycopg2-binary cryptography python-dotenv
```

#### Authentication Issues
- Master passwords are case-sensitive
- Username and master password combination must match exactly
- If you get "encryption errors," verify you're using the correct master password

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

## Advanced Configuration

### Database Administration

For database monitoring and maintenance, connect directly to your PostgreSQL instance from EC2:

```bash
psql -h your-db-host -p 5432 -U your-db-admin -d password_manager
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

-- View all users and their stored passwords (encrypted)
SELECT 
  u.id AS user_id,
  u.username AS username,
  sp.website,
  sp.username AS account_username,
  sp.encrypted_password
FROM users u
JOIN stored_passwords sp ON u.id = sp.user_id
ORDER BY u.id;
```

### Backup and Restore

Run these commands from your EC2 instance:

```bash
# Create backup
pg_dump -h your-db-host -p 5432 -U your-db-admin -d password_manager > backup.sql

# Restore from backup
psql -h your-db-host -p 5432 -U your-db-admin -d password_manager < backup.sql
```

## Important Security Notes

⚠️ **Critical Security Information**

- **Terminal privacy**: Ensure you're in a private terminal session when viewing passwords
- **Master password**: This is never stored anywhere. If you forget it, your data cannot be recovered
- **Screen privacy**: Passwords are displayed in plain text in the terminal - ensure no one is watching
- **Terminal history**: Consider using `history -c` after use to clear command history
- **SSH security**: Always use SSH keys instead of passwords for EC2 access
- **Database isolation**: RDS is private and not accessible from the internet
- **Network security**: Database connections use SSL/TLS encryption
- **Environment variables**: Keep your `.env` file secure and never commit it to version control
- **SSH Keys**: Never commit your `.pem` key files to version control
- **Database credentials**: Use strong passwords and limit access
- **Screen sessions**: Be careful with screen/tmux sessions that might persist passwords

## Development History

This password manager has evolved through multiple versions:
- **V1**: Single-user with file-based salt storage
- **V2**: Multi-user with JSON file storage
- **V3**: PostgreSQL-based multi-user system with AWS deployment
- **V4**: Current version consisting of V3 + Delete function

The current version provides better security, scalability, and reliability compared to previous file-based approaches.

## Disclaimer

This software is provided as-is. While it implements industry-standard security practices, use it at your own risk. Always maintain proper backups and follow security best practices. The private database configuration is required for production use.
