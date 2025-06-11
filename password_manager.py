import base64 # encode derived key in the format Fernet expects (URL-safe base64)
import os #use for os.urandom() to generate random bytes for the salt
# import json 
import hashlib # create hashes w/ username + master_password
from cryptography.fernet import Fernet #encryption class
from cryptography.hazmat.primitives import hashes #hashing algorithms 'SHA256'
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC #key derivation func that turns pass ~> proper encryption keys
from psycopg2.extras import RealDictCursor
import boto3
import psycopg2
from botocore.exceptions import ClientError
from dotenv import load_dotenv


'''
Password manager V2 logic (changed due to security improvements--changing to a multi-user approach)

def generate_master_key_setup():
    """
    generate a salt and store it. only runs once to set up the system. 
    (salt not secret but has to stay consistent throughout--thus runs once)
    """
    salt = os.urandom(16)  #16 random bytes via os crypto secure rand # gen (16 byes standard for PBKDF2 salts & good security)
    with open("salt.key", "wb") as salt_file:
        salt_file.write(salt)
    print("Master key setup is complete. Salt has been generated and saved.")

def load_salt():
    """load salt from file"""
    try:
        with open("salt.key", "rb") as salt_file:
            return salt_file.read()
    except FileNotFoundError:
        print("Salt file not found. Run setup func. first")
        return None
"""


"""
Version 3, using json files as data storage.

def get_user_filename(username, master_password):
    """
    generates a filename based on master_password hash.
    two-factor identification through username and master-password
    """
    combined = f"{username}:{master_password}"
    password_hash = hashlib.sha256(combined.encode()).hexdigest()
    return f"user_{password_hash}.json"

def load_or_create_user_data(username, master_password):
    filename = get_user_filename(username, master_password)

    if os.path.exists(filename):
        # Load existing user data
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                return data["salt"], data.get("passwords", []), filename
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Corrupted user file: {filename}. Error: {e}")
            return None, None, None
    else:
        # User file doesn't exist - check if they have an existing account
        print(f"\nNo account found for username '{username}' with the provided password.")
        
        while True:
            has_account = input("Do you have an existing account? (yes/no): ").lower().strip()
            
            if has_account in ['yes', 'y']:
                print("Either your username or password is incorrect.")
                print("Please check your credentials and try again.")
                return None, None, None
            elif has_account in ['no', 'n']:
                print(f"\nCreating new account for '{username}'...")
                break
            else:
                print("Please enter 'yes' or 'no'.")
        
        # Create new user with unique generated salt
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
        user_data = {
            "salt": salt,
            "passwords": []
        }
        # Store new file
        with open(filename, "w") as f:
            json.dump(user_data, f, indent=2)
        print(f"New user created! Data will be stored in {filename}")
        return salt, [], filename

def save_user_data(filename, salt, passwords):
    """Save user data into specified file"""
    user_data = {
        "salt": salt,
        "passwords": passwords
    }
    with open(filename, "w") as f:
        json.dump(user_data, f, indent=2)

def derive_key_from_master_password(master_password, salt):
    """
    Derive a fernet key from master password via PBKDF2 (core security func)
    """
    # Convert base64 salt string back to bytes
    salt_bytes = base64.b64decode(salt.encode('utf-8'))

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # 32 bytes for Fernet
        salt=salt_bytes,  # Use the actual salt bytes
        iterations=1_200_000, #high it count to account for brute force 
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
    return key

def view_passwords(passwords, fer):
    """View all stored passwords for this user"""
    col1_width, col2_width, col3_width = 30, 30, 30
    
    print("\n--- Your Stored Passwords ---")
    print(f"{'Website'.ljust(col1_width)} {'Username'.ljust(col2_width)} {'Password'.ljust(col3_width)}")
    print('-' * (col1_width + col2_width + col3_width))
    
    if not passwords:
        print("No passwords stored yet.")
        return
    
    for entry in passwords:
        try:
            website = entry["website"]
            username = entry["username"]
            encrypted_password = entry["password"]
            
            # Decrypt the password
            decrypted_pass = fer.decrypt(encrypted_password.encode('utf-8')).decode('utf-8')
            print(f"{website.ljust(col1_width)} {username.ljust(col2_width)} {decrypted_pass.ljust(col3_width)}")
            
        except Exception as e:
            print(f"Error decrypting entry for {entry.get('website', 'unknown')}: {e}")
    
    print("--- End of Passwords ---\n")

def add_password(passwords, fer, filename, salt):
    """Add a new password for this user"""
    website_name = input("Website name: ")
    username = input("Account name: ")
    password = input("Password: ")
    
    # Encrypt the password
    encrypted_password = fer.encrypt(password.encode('utf-8')).decode('utf-8')
    
    # Add to passwords list
    new_entry = {
        "website": website_name,
        "username": username,
        "password": encrypted_password
    }
    
    passwords.append(new_entry)
    
    # Save to file
    save_user_data(filename, salt, passwords)
    print("Password added successfully!")

def main():
    print("=== Multi-User Password Manager ===")
    
    while True:
        # Get username and master password
        username = input("Enter your username: ")
        master_pwd = input("Enter your master password: ")
        
        # Load or create user data
        salt, passwords, filename = load_or_create_user_data(username, master_pwd)
        
        if salt is None:
            print("Please try again with correct credentials.\n")
            continue  # Go back to login prompt
        
        # Derive encryption key
        try:
            key = derive_key_from_master_password(master_pwd, salt)
            fer = Fernet(key)
            
            # Test the key by trying to decrypt existing passwords if any
            if passwords:
                # Try to decrypt the first password to verify the key works
                test_entry = passwords[0]
                fer.decrypt(test_entry["password"].encode('utf-8'))
                print("Master password accepted - existing data verified.")
            else:
                # for new users, just test basic encryption/decryption
                test_token = fer.encrypt(b"test")
                fer.decrypt(test_token)
                print("Master password accepted - new user verified.")
            
            break  # Exit login loop on success
            
        except Exception as e:
            print(f"Invalid master password or encryption error: {e}")
            print("If this is an existing user, make sure you're using the exact same username and password.")
            continue  # Go back to login prompt
    
    # Main program loop
    while True:
        mode = input("\nWould you like to add a new password or view existing ones (view/add), press q to quit? ").lower().strip()
        
        if mode == "q":
            break
        elif mode == "view":
            view_passwords(passwords, fer)
        elif mode == "add":
            add_password(passwords, fer, filename, salt)
        else:
            print("Invalid mode. Please enter 'view', 'add', or 'q'.")

if __name__ == "__main__":
    main()
'''

# Load environment variables
load_dotenv()

class PostgreSQLPasswordManager:
    def __init__(self):
        # AWS RDS connection parameters
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'sslmode': 'require'  # Force SSL connection
        }
        self.connection = None
        
    def connect_to_database(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            return True
        except psycopg2.Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, password_hash)
        );
        """
        
        create_passwords_table = """
        CREATE TABLE IF NOT EXISTS stored_passwords (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            website VARCHAR(255) NOT NULL,
            username VARCHAR(255) NOT NULL,
            encrypted_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_users_table)
                cursor.execute(create_passwords_table)
                self.connection.commit()
                print("Database tables created successfully!")
        except psycopg2.Error as e:
            print(f"Error creating tables: {e}")
            self.connection.rollback()

    def get_user_id(self, username, master_password):
        """Get user ID based on username and master password hash"""
        combined = f"{username}:{master_password}"
        password_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT id, salt FROM users WHERE username = %s AND password_hash = %s",
                    (username, password_hash)
                )
                result = cursor.fetchone()
                if result:
                    return result['id'], result['salt']
                else:
                    return None, None
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None, None

    def create_user(self, username, master_password):
        """Create a new user account"""
        combined = f"{username}:{master_password}"
        password_hash = hashlib.sha256(combined.encode()).hexdigest()
        salt = base64.b64encode(os.urandom(16)).decode('utf-8')
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s) RETURNING id",
                    (username, password_hash, salt)
                )
                user_id = cursor.fetchone()[0]
                self.connection.commit()
                print(f"New user created successfully! User ID: {user_id}")
                return user_id, salt
        except psycopg2.IntegrityError:
            self.connection.rollback()
            print("User already exists with these credentials.")
            return None, None
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error creating user: {e}")
            return None, None

    def load_or_create_user_data(self, username, master_password):
        """Load existing user or create new one"""
        user_id, salt = self.get_user_id(username, master_password)
        
        if user_id is not None:
            # Load existing passwords
            passwords = self.get_user_passwords(user_id)
            return user_id, salt, passwords
        else:
            # Check if user wants to create new account
            print(f"\nNo account found for username '{username}' with the provided password.")
            
            while True:
                has_account = input("Do you have an existing account? (yes/no): ").lower().strip()
                
                if has_account in ['yes', 'y']:
                    print("Either your username or password is incorrect.")
                    return None, None, None
                elif has_account in ['no', 'n']:
                    print(f"\nCreating new account for '{username}'...")
                    user_id, salt = self.create_user(username, master_password)
                    if user_id:
                        return user_id, salt, []
                    else:
                        return None, None, None
                else:
                    print("Please enter 'yes' or 'no'.")

    def get_user_passwords(self, user_id):
        """Retrieve all passwords for a specific user"""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT website, username, encrypted_password FROM stored_passwords WHERE user_id = %s ORDER BY website",
                    (user_id,)
                )
                return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error retrieving passwords: {e}")
            return []

    def add_password(self, user_id, website, username, encrypted_password):
        """Add a new password entry for a user"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO stored_passwords (user_id, website, username, encrypted_password) 
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, website, username, encrypted_password)
                )
                self.connection.commit()
                print("Password added successfully!")
                return True
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error adding password: {e}")
            return False

    def derive_key_from_master_password(self, master_password, salt):
        """Derive encryption key from master password"""
        salt_bytes = base64.b64decode(salt.encode('utf-8'))
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=1_200_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
        return key

    def view_passwords(self, passwords, fer):
        """Display all stored passwords"""
        col1_width, col2_width, col3_width = 30, 30, 30
        
        print("\n--- Your Stored Passwords ---")
        print(f"{'Website'.ljust(col1_width)} {'Username'.ljust(col2_width)} {'Password'.ljust(col3_width)}")
        print('-' * (col1_width + col2_width + col3_width))
        
        if not passwords:
            print("No passwords stored yet.")
            return
        
        for entry in passwords:
            try:
                website = entry["website"]
                username = entry["username"]
                encrypted_password = entry["encrypted_password"]
                
                # Decrypt the password
                decrypted_pass = fer.decrypt(encrypted_password.encode('utf-8')).decode('utf-8')
                print(f"{website.ljust(col1_width)} {username.ljust(col2_width)} {decrypted_pass.ljust(col3_width)}")
                
            except Exception as e:
                print(f"Error decrypting entry for {entry.get('website', 'unknown')}: {e}")
        
        print("--- End of Passwords ---\n")

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

def main():
    print("=== PostgreSQL Multi-User Password Manager ===")
    
    # Initialize password manager
    pm = PostgreSQLPasswordManager()
    
    if not pm.connect_to_database():
        print("Failed to connect to database. Exiting.")
        return
    
    # Create tables if they don't exist
    pm.create_tables()
    
    try:
        while True:
            # Get username and master password
            username = input("Enter your username: ")
            master_pwd = input("Enter your master password: ")
            
            # Load or create user data
            user_id, salt, passwords = pm.load_or_create_user_data(username, master_pwd)
            
            if user_id is None:
                print("Please try again with correct credentials.\n")
                continue
            
            # Derive encryption key
            try:
                key = pm.derive_key_from_master_password(master_pwd, salt)
                fer = Fernet(key)
                
                # Test the key
                if passwords:
                    test_entry = passwords[0]
                    fer.decrypt(test_entry["encrypted_password"].encode('utf-8'))
                    print("Master password accepted - existing data verified.")
                else:
                    test_token = fer.encrypt(b"test")
                    fer.decrypt(test_token)
                    print("Master password accepted - new user verified.")
                
                break
                
            except Exception as e:
                print(f"Invalid master password or encryption error: {e}")
                continue
        
        # Main program loop
        while True:
            mode = input("\nWould you like to add a new password or view existing ones (view/add), press q to quit? ").lower().strip()
            
            if mode == "q":
                break
            elif mode == "view":
                pm.view_passwords(passwords, fer)
            elif mode == "add":
                website_name = input("Website name: ")
                account_username = input("Account name: ")
                password = input("Password: ")
                
                # Encrypt the password
                encrypted_password = fer.encrypt(password.encode('utf-8')).decode('utf-8')
                
                # Add to database
                if pm.add_password(user_id, website_name, account_username, encrypted_password):
                    # Refresh passwords list
                    passwords = pm.get_user_passwords(user_id)
            else:
                print("Invalid mode. Please enter 'view', 'add', or 'q'.")
    
    finally:
        pm.close_connection()

if __name__ == "__main__":
    main()
