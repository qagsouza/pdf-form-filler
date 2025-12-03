#!/usr/bin/env python
"""
Script to migrate existing users to RBAC roles based on their legacy role field
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('pdf_form_filler.db')
cursor = conn.cursor()

try:
    # Get role IDs
    cursor.execute("SELECT id, name FROM roles ORDER BY name")
    roles_data = cursor.fetchall()

    if not roles_data:
        print("❌ Roles não encontrados. Execute as migrações do banco de dados primeiro:")
        print("   alembic upgrade head")
        exit(1)

    roles = {name: role_id for role_id, name in roles_data}

    print(f"✓ Roles encontrados:")
    for name, role_id in roles.items():
        print(f"  - {name}: {role_id}")
    print()

    # Get all users
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    print(f"Encontrados {len(users)} usuários\n")

    migrated_count = 0
    skipped_count = 0

    for user_id, username, legacy_role in users:
        # Check if user already has roles assigned
        cursor.execute("SELECT COUNT(*) FROM user_roles WHERE user_id = ?", (user_id,))
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"⊘ {username} - já possui {existing_count} role(s) atribuído(s)")
            skipped_count += 1
            continue

        # Assign role based on legacy role field
        if legacy_role == "admin" and "admin" in roles:
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, roles["admin"])
            )
            print(f"✓ {username} - migrado para role 'admin'")
            migrated_count += 1
        elif "viewer" in roles:
            # Default users get viewer role
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, roles["viewer"])
            )
            print(f"✓ {username} - migrado para role 'viewer'")
            migrated_count += 1
        else:
            print(f"⚠ {username} - role 'viewer' não encontrado, pulando")
            skipped_count += 1

    conn.commit()

    print(f"\n{'='*50}")
    print(f"Migração concluída!")
    print(f"  ✓ {migrated_count} usuário(s) migrado(s)")
    print(f"  ⊘ {skipped_count} usuário(s) já tinham roles ou foram pulados")
    print(f"{'='*50}")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro durante a migração: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()
