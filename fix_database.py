import sqlite3
import os

# Database path
db_path = 'instance/digital_agriculture.db'

if os.path.exists(db_path):
    print(f"Updating database at {db_path}...")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if updated_at column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            print("Adding updated_at column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
            print("updated_at column added successfully!")
        else:
            print("updated_at column already exists.")
            
        conn.commit()
        print("Database updated successfully!")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()
else:
    print(f"Database file not found at {db_path}")
    print("Please run 'python init_db.py' first to create the database.")
