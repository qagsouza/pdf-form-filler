#!/usr/bin/env python3
"""
Script to inspect all properties of PDF form fields
"""
import sys
from pypdf import PdfReader

if len(sys.argv) < 2:
    print("Usage: python inspect_pdf_fields.py <pdf_file>")
    sys.exit(1)

pdf_path = sys.argv[1]

print(f"Inspecting PDF: {pdf_path}\n")
print("=" * 80)

reader = PdfReader(pdf_path)

for page_idx, page in enumerate(reader.pages):
    if "/Annots" not in page:
        continue

    print(f"\nPage {page_idx + 1}")
    print("-" * 80)

    annots = page["/Annots"]
    for idx, annot_ref in enumerate(annots):
        annot = annot_ref.get_object()

        # Get field name
        name = annot.get("/T")
        if name:
            name = str(name).strip("()")

        print(f"\nField #{idx + 1}: {name}")
        print("  Properties:")

        # List all available keys
        for key in annot.keys():
            value = annot.get(key)

            # Format value for display
            if key in ["/T", "/TU", "/TM", "/V"]:
                value_str = str(value).strip("()")
            elif key == "/Rect":
                value_str = f"[{', '.join(str(v) for v in value)}]"
            elif key == "/Opt":
                try:
                    value_str = [str(o).strip("()") for o in value]
                except:
                    value_str = str(value)
            else:
                value_str = str(value)[:100]

            print(f"    {key}: {value_str}")

print("\n" + "=" * 80)
print("\nKey field properties to look for:")
print("  /T   - Field name")
print("  /TU  - Tooltip/User text (label/description)")
print("  /TM  - Tooltip modified")
print("  /FT  - Field type (/Tx=text, /Btn=button, /Ch=choice)")
print("  /V   - Value")
print("  /DV  - Default value")
print("  /Rect - Rectangle coordinates")
print("  /Opt - Options for choice fields")
