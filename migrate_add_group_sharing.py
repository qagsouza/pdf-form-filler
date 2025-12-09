"""
Migration script to add group_id column to template_shares table
"""
import sqlite3

def migrate():
    """Add group_id column to template_shares table"""
    conn = sqlite3.connect('pdf_form_filler.db')
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(template_shares)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'group_id' not in columns:
            print("Adding group_id column to template_shares...")

            # Add group_id column
            cursor.execute("""
                ALTER TABLE template_shares
                ADD COLUMN group_id VARCHAR
                REFERENCES groups(id) ON DELETE CASCADE
            """)

            # Make user_id nullable by recreating the table
            print("Making user_id nullable...")

            # Get all existing data
            cursor.execute("SELECT * FROM template_shares")
            shares = cursor.fetchall()

            # Drop old table
            cursor.execute("DROP TABLE template_shares")

            # Create new table with proper schema
            cursor.execute("""
                CREATE TABLE template_shares (
                    id VARCHAR NOT NULL,
                    template_id VARCHAR NOT NULL,
                    user_id VARCHAR,
                    group_id VARCHAR,
                    shared_by_id VARCHAR,
                    permission VARCHAR NOT NULL,
                    created_at DATETIME NOT NULL,
                    PRIMARY KEY (id),
                    FOREIGN KEY(template_id) REFERENCES templates (id) ON DELETE CASCADE,
                    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY(group_id) REFERENCES groups (id) ON DELETE CASCADE,
                    FOREIGN KEY(shared_by_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)

            # Insert data back (only with user_id, group_id will be NULL)
            for share in shares:
                cursor.execute("""
                    INSERT INTO template_shares
                    (id, template_id, user_id, group_id, shared_by_id, permission, created_at)
                    VALUES (?, ?, ?, NULL, ?, ?, ?)
                """, share)

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
