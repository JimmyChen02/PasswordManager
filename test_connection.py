import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test connection to PostgreSQL database"""
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'sslmode': 'require'
    }
    
    try:
        print("Attempting to connect to database...")
        print(f"Host: {db_config['host']}")
        print(f"Database: {db_config['database']}")
        print(f"User: {db_config['user']}")
        
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"Connection successful!")
        print(f"PostgreSQL version: {version}")
        
        # Test creating a simple table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_message VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert test data
        cursor.execute(
            "INSERT INTO connection_test (test_message) VALUES (%s)",
            ("Connection test successful!",)
        )
        
        # Read test data
        cursor.execute("SELECT test_message, created_at FROM connection_test ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        print(f"Database operations successful!")
        print(f"Test message: {result[0]}")
        print(f"Created at: {result[1]}")
        
        # Clean up
        cursor.execute("DROP TABLE connection_test")
        connection.commit()
        
        cursor.close()
        connection.close()
        print("Connection test completed successfully!")
        
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== PostgreSQL Connection Test ===")
    if test_connection():
        print("\nYour database is ready for the password manager!")
    else:
        print("\nPlease check your configuration and try again.")