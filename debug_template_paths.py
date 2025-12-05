#!/usr/bin/env python3
"""
Debug script to check template paths in database vs filesystem
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text

# Database path
db_path = "pdf_form_filler.db"
engine = create_engine(f"sqlite:///{db_path}")

print("=" * 80)
print("Checking Template Paths")
print("=" * 80)

# Query all templates
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, file_path, original_filename FROM templates"))
    templates = result.fetchall()

    print(f"\nFound {len(templates)} templates in database:\n")

    for template in templates:
        template_id, name, file_path, original_filename = template
        print(f"Template: {name}")
        print(f"  ID: {template_id}")
        print(f"  file_path in DB: {file_path}")
        print(f"  original_filename: {original_filename}")

        # Check if file exists at various possible paths
        possible_paths = [
            file_path,
            f"storage/{file_path}",
            f"storage/templates/{file_path}",
            f"storage/templates/{template_id}/{original_filename}",
        ]

        print(f"  Checking possible file locations:")
        found = False
        for path in possible_paths:
            exists = os.path.exists(path)
            if exists:
                size = os.path.getsize(path)
                print(f"    ✓ EXISTS: {path} ({size} bytes)")
                found = True
            else:
                print(f"    ✗ NOT FOUND: {path}")

        if not found:
            print(f"  ⚠️ WARNING: File not found at any expected location!")

        print()

print("=" * 80)
print("Checking storage/templates directory structure:")
print("=" * 80)

storage_path = Path("storage/templates")
if storage_path.exists():
    print(f"\nContents of {storage_path}:")
    for item in sorted(storage_path.rglob("*")):
        if item.is_file():
            size = item.stat().st_size
            print(f"  {item.relative_to(storage_path)} ({size} bytes)")
else:
    print(f"\n⚠️ Directory {storage_path} does not exist!")

print()
