
import sqlite3

DB_FILE = "pkf_database.db"

def add_gender_column():
    """
    Adds the 'gender' column to the 'members' table if it doesn't exist.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Check if the column already exists
        cursor.execute("PRAGMA table_info(members)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'gender' not in columns:
            print("Adding 'gender' column to 'members' table...")
            cursor.execute("ALTER TABLE members ADD COLUMN gender TEXT")
            print("'gender' column added successfully.")
        else:
            print("'gender' column already exists.")

        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_gender_column()
