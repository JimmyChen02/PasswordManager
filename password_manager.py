import base64 # encode derived key in the format Fernet expects (URL-safe base64)
import os #use for os.urandom() to generate random bytes for the salt
import json 
import hashlib # create hashes w/ username + master_password
from cryptography.fernet import Fernet #encryption class
from cryptography.hazmat.primitives import hashes #hashing algorithms 'SHA256'
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC #key derivation func that turns pass ~> proper encryption keys

"""
Password manager V2 logic (changed due to security improvements--changing to a multi-user approach)

def generate_master_key_setup():
    '''
    generate a salt and store it. only runs once to set up the system. 
    (salt not secret but has to stay consistent throughout--thus runs once)
    '''
    salt = os.urandom(16)  #16 random bytes via os crypto secure rand # gen (16 byes standard for PBKDF2 salts & good security)
    with open("salt.key", "wb") as salt_file:
        salt_file.write(salt)
    print("Master key setup is complete. Salt has been generated and saved.")

def load_salt():
    '''load salt from file'''
    try:
        with open("salt.key", "rb") as salt_file:
            return salt_file.read()
    except FileNotFoundError:
        print("Salt file not found. Run setup func. first")
        return None
"""

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