#!/usr/bin/env python3
"""
Script to update template field cache with rect coordinates
"""
import sqlite3
from pathlib import Path

from src.pdf_form_filler.core import PDFFormFiller
from src.pdf_form_filler.services.storage_service import StorageService

# Connect to database
db_path = Path("pdf_form_filler.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all templates
cursor.execute("SELECT id, file_path FROM templates")
templates = cursor.fetchall()

storage = StorageService()

for template_id, file_path in templates:
    print(f"Processing template {template_id}...")

    try:
        # Get absolute path
        absolute_path = storage.get_template_path(file_path)

        # Extract fields with new rect data
        pdf_filler = PDFFormFiller(str(absolute_path))
        fields = pdf_filler.fields

        # Update database
        import json
        cursor.execute(
            "UPDATE templates SET fields_metadata = ? WHERE id = ?",
            (json.dumps(fields), template_id)
        )

        print(f"  ✓ Updated {len(fields)} fields")

    except Exception as e:
        print(f"  ✗ Error: {e}")

# Commit changes
conn.commit()
conn.close()

print("\nDone! Template cache updated.")
