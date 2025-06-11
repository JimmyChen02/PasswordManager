# PostgreSQL Password Manager

A secure multi-user password manager using PostgreSQL and encryption.

## Features
- Multi-user support with unique encryption keys
- PBKDF2 key derivation with high iteration count
- Fernet encryption for stored passwords
- PostgreSQL database backend

## Setup
1. Copy `.env.example` to `.env`
2. Fill in your actual database credentials in `.env`
3. Install dependencies: `pip3 install psycopg2-binary cryptography python-dotenv boto3`
4. Run: `python3 password_manager.py`

## Database Setup
The script automatically creates the necessary tables on first run.# PasswordManager
