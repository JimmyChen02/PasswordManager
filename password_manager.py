import base64 # encode derived key in the format Fernet expects (URL-safe base64)
import os #use for os.urandom() to generate random bytes for the salt
from cryptography.fernet import Fernet #encryption class
from cryptography.hazmat.primitives import hashes #hashing algorithms 'SHA256'
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC #key derivation func that turns pass ~> proper encryption keys


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

def derive_key_from_master_password(master_password, salt):
    '''
    derive a fernet key from master password via PBKDF2 (core security func)
    '''
    kdf = PBKDF2HMAC( #key derivation func obj
        algorithm = hashes.SHA256(), #SHA256 hashing algo
        length = 32, #output 32 bytes for Fernet req
        salt = salt,
        iterations = 1_200_000, #high iteration count for security
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
    return key

def view():
    """View all stored passwords"""
    try:
        with open("passwords.txt", "r") as f:
            lines = f.readlines()
            if not lines:
                print("No passwords stored yet.")
                return
            
            print("\n--- Stored Passwords ---")
            for line in lines:
                if line.strip():  # Skip empty lines
                    data = line.rstrip()
                    try:
                        user, passw = data.split("|", 1)  # Split only on first |
                        decrypted_pass = fer.decrypt(passw.encode()).decode()
                        print("User:", user, "| Password:", decrypted_pass)
                    except ValueError:
                        print("Malformed entry:", data)
                    except Exception as e:
                        print("Decryption failed for user:", user)
            print("--- End of Passwords ---\n")
                        
    except FileNotFoundError:
        print("No passwords stored yet. Add some passwords first!")


def add():
    """Add a new password"""
    name = input("Account name: ")
    pwd = input("Password: ")

    with open("passwords.txt", 'a') as f:
        f.write(name + "|" + fer.encrypt(pwd.encode()).decode() + "\n")

# Check if this is first time setup
if not os.path.exists("salt.key"):
    print("First time setup detected.")
    generate_master_key_setup()

# Load salt
salt = load_salt()
if salt is None:
    exit("Setup failed. Exiting.")

# Get master password and derive key
master_pwd = input("What is the master password? ")
key = derive_key_from_master_password(master_pwd, salt)

try:
    fer = Fernet(key)
    # Test the key by trying to encrypt/decrypt a test string
    test_token = fer.encrypt(b"test")
    fer.decrypt(test_token)
    print("Master password accepted.")
except Exception as e:
    print("Invalid master password or corrupted key.")
    exit()

# Main program loop
while True:
    mode = input("\nWould you like to add a new password or view existing ones (view, add), press q to quit? ").lower().strip()
    
    if mode == "q":
        break
    elif mode == "view":
        view()
    elif mode == "add":
        add()
    else: 
        print("Invalid mode. Please enter 'view', 'add', or 'q'.")