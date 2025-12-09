"""
Migration script to add group_id column to templates table
"""
import sqlite3

def migrate():
    """Add group_id column to templates table"""
    conn = sqlite3.connect('pdf_form_filler.db')
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(templates)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'group_id' not in columns:
            print("Adding group_id column to templates...")

            # Add group_id column (nullable, not required)
            cursor.execute("""
                ALTER TABLE templates
                ADD COLUMN group_id VARCHAR
                REFERENCES groups(id) ON DELETE SET NULL
            """)

            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Column group_id already exists. Nothing to do.")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
