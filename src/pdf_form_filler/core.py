"""
Core functionality for PDF Form Filler
"""
import os
from typing import Dict, List, Optional, Union, Any
import pdfrw
from pypdf import PdfReader as PyPdfReader

from .errors import (
    PDFNotFoundError,
    PDFPermissionError,
    PDFParseError,
    InvalidDataError,
    InvalidFieldError,
    PDFFormFillerError,
)


class PDFFormFiller:
    """
    Main class for filling PDF forms with support for text fields, checkboxes, and radio buttons.

    Example:
        >>> filler = PDFFormFiller("input.pdf")
        >>> filler.fill({"name": "John Doe", "agree": True})
        >>> filler.save("output.pdf", flatten=True)
    """

    def __init__(self, input_pdf: str):
        """
        Initialize PDF Form Filler with input PDF

        Args:
            input_pdf: Path to input PDF file

        Raises:
            PDFNotFoundError: If input PDF doesn't exist
            PDFParseError: If PDF cannot be parsed
            PDFPermissionError: If no read permission for PDF
        """
        self._validate_input_pdf(input_pdf)

        try:
            self.template_pdf = pdfrw.PdfReader(input_pdf)
            self.input_pdf = input_pdf
            self.fields = self._extract_fields_detailed()
        except pdfrw.PdfParseError as e:
            raise PDFParseError(f"Failed to parse PDF: {e}")
        except Exception as e:
            raise PDFFormFillerError(f"Unexpected error loading PDF: {e}")

    def _validate_input_pdf(self, input_pdf: str) -> None:
        """Validate input PDF file"""
        if not os.path.exists(input_pdf):
            raise PDFNotFoundError(f"PDF file not found: {input_pdf}")

        if not os.path.isfile(input_pdf):
            raise PDFNotFoundError(f"Path is not a file: {input_pdf}")

        if not os.access(input_pdf, os.R_OK):
            raise PDFPermissionError(f"No read permission for file: {input_pdf}")

    def _extract_fields_detailed(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract all form fields with detailed type information using pypdf.
        Falls back to pdfrw if pypdf fails.

        Returns:
            Dictionary mapping field names to their metadata
        """
        fields = {}

        # Try using pypdf for better type detection
        try:
            reader = PyPdfReader(self.input_pdf)
            for page_idx, page in enumerate(reader.pages):
                if "/Annots" not in page:
                    continue

                annots = page["/Annots"]
                for annot_ref in annots:
                    annot = annot_ref.get_object()
                    name = annot.get("/T")
                    if not name:
                        continue

                    name = str(name).strip("()")
                    field_type = annot.get("/FT")

                    # Determine field type
                    if field_type:
                        ft_str = str(field_type)
                        if "/Btn" in ft_str:
                            ftype = "button"
                        elif "/Tx" in ft_str:
                            ftype = "text"
                        elif "/Ch" in ft_str:
                            ftype = "choice"
                        else:
                            ftype = "unknown"
                    else:
                        ftype = "unknown"

                    # Get current value if exists
                    current_value = annot.get("/V", "")
                    if current_value:
                        current_value = str(current_value)

                    fields[name] = {
                        "type": ftype,
                        "page": page_idx,
                        "value": current_value,
                    }

        except Exception:
            # Fallback to pdfrw extraction
            fields = self._extract_fields_pdfrw()

        return fields

    def _extract_fields_pdfrw(self) -> Dict[str, Dict[str, Any]]:
        """Fallback method using pdfrw for field extraction"""
        fields = {}

        for page_num, page in enumerate(self.template_pdf.pages):
            annotations = page.get("/Annots")
            if not annotations:
                continue

            for annotation in annotations:
                field = annotation.get("/T")
                if not field:
                    continue

                field_name = field[1:-1]  # Remove parentheses
                field_type = annotation.get("/FT", "/Tx")

                # Convert pdfrw type to string
                if hasattr(field_type, "__str__"):
                    ft_str = str(field_type)
                    if "/Btn" in ft_str:
                        ftype = "button"
                    elif "/Tx" in ft_str:
                        ftype = "text"
                    elif "/Ch" in ft_str:
                        ftype = "choice"
                    else:
                        ftype = "unknown"
                else:
                    ftype = "text"

                fields[field_name] = {
                    "type": ftype,
                    "page": page_num,
                    "field_type": field_type,
                    "annotation": annotation,
                }

        return fields

    def get_available_fields(self) -> List[str]:
        """
        Get list of all available form fields

        Returns:
            List of field names
        """
        return list(self.fields.keys())

    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific field

        Args:
            field_name: Name of the field

        Returns:
            Dictionary with field information

        Raises:
            InvalidFieldError: If field doesn't exist
        """
        if field_name not in self.fields:
            raise InvalidFieldError(f"Field '{field_name}' not found in PDF")

        return self.fields[field_name]

    def get_field_type(self, field_name: str) -> str:
        """
        Get the type of a specific field

        Args:
            field_name: Name of the field

        Returns:
            Field type: 'text', 'button', 'choice', or 'unknown'

        Raises:
            InvalidFieldError: If field doesn't exist
        """
        info = self.get_field_info(field_name)
        return info.get("type", "unknown")

    def fill(self, data: Dict[str, Union[str, bool, int]]) -> None:
        """
        Fill form with provided data

        Args:
            data: Dictionary with field names as keys and values to fill

        Raises:
            InvalidDataError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise InvalidDataError("Data must be a dictionary")

        # Warn about unused fields
        unused_fields = set(data.keys()) - set(self.fields.keys())
        if unused_fields:
            print(
                f"Warning: The following fields were not found in PDF: "
                f"{sorted(list(unused_fields))}"
            )

        # Fill each field
        for field_name, value in data.items():
            if field_name in self.fields:
                self._set_field_value(field_name, value)

    def _set_field_value(self, field_name: str, value: Union[str, bool, int]) -> None:
        """Set value for a specific field"""
        # Find the annotation in pdfrw template
        annotation = None
        field_type = None

        for page in self.template_pdf.pages:
            annotations = page.get("/Annots")
            if not annotations:
                continue

            for annot in annotations:
                field = annot.get("/T")
                if not field:
                    continue

                name = field[1:-1] if isinstance(field, str) else field.to_unicode()
                if name == field_name:
                    annotation = annot
                    field_type = annot.get("/FT")
                    break

            if annotation:
                break

        if not annotation:
            print(f"Warning: Could not find annotation for field '{field_name}'")
            return

        try:
            # Determine field type
            ft_str = str(field_type) if field_type else ""

            if "/Btn" in ft_str:
                # Button field (checkbox/radio)
                self._set_button_value(annotation, value)
            elif "/Ch" in ft_str:
                # Choice field (dropdown/listbox)
                self._set_choice_value(annotation, value)
            else:
                # Text field (default)
                self._set_text_value(annotation, value)

        except Exception as e:
            print(f"Warning: Could not set value for field '{field_name}': {e}")

    def _set_text_value(self, annotation: Any, value: Union[str, int]) -> None:
        """Set value for text field"""
        annotation.update(pdfrw.PdfDict(V=str(value)))

    def _set_button_value(self, annotation: Any, value: Union[bool, str]) -> None:
        """Set value for button field (checkbox/radio)"""
        # Normalize value to export value name
        if isinstance(value, bool):
            export = "Yes" if value else "Off"
        elif str(value).lower() in ("on", "yes", "true", "1"):
            export = "Yes"
        elif str(value).lower() in ("off", "no", "false", "0", ""):
            export = "Off"
        else:
            export = str(value)

        # Set both V (value) and AS (appearance state)
        annotation.update(
            pdfrw.PdfDict(V=pdfrw.PdfName(export), AS=pdfrw.PdfName(export))
        )

    def _set_choice_value(self, annotation: Any, value: Union[str, int]) -> None:
        """Set value for choice field (dropdown/listbox)"""
        annotation.update(pdfrw.PdfDict(V=str(value)))

    def save(self, output_pdf: str, flatten: bool = False) -> None:
        """
        Save filled PDF to output file

        Args:
            output_pdf: Path for output PDF file
            flatten: If True, remove form fields making the PDF static

        Raises:
            PDFPermissionError: If no write permission for output directory
        """
        output_dir = os.path.dirname(output_pdf) or "."

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        if os.path.exists(output_pdf) and not os.access(output_pdf, os.W_OK):
            raise PDFPermissionError(f"No write permission for file: {output_pdf}")

        # Apply flatten if requested
        if flatten:
            self._flatten_form()

        try:
            writer = pdfrw.PdfWriter()
            writer.write(output_pdf, self.template_pdf)
        except Exception as e:
            raise PDFFormFillerError(f"Failed to save PDF: {e}")

    def _flatten_form(self) -> None:
        """
        Flatten the form by marking fields as read-only.
        This makes the PDF non-editable but preserves the values.

        Note: True flattening (removing fields entirely) would require
        rendering the field values as content, which pdfrw doesn't support well.
        This approach sets the ReadOnly flag on all fields instead.
        """
        # Set all fields to read-only instead of removing them
        for page in self.template_pdf.pages:
            annotations = page.get("/Annots")
            if not annotations:
                continue

            for annot in annotations:
                # Set ReadOnly flag
                if annot.get("/FT"):  # Is a form field
                    # Get current flags or initialize to 0
                    flags = annot.get("/Ff")
                    if flags:
                        flags = int(flags)
                    else:
                        flags = 0

                    # Set ReadOnly bit (bit 0 = 1)
                    flags = flags | 1

                    # Update annotation
                    annot.update(pdfrw.PdfDict(Ff=str(flags)))

        # Mark the form as NeedAppearances to ensure values are displayed
        if self.template_pdf.Root and self.template_pdf.Root.AcroForm:
            self.template_pdf.Root.AcroForm.update(
                pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true'))
            )


# Convenience function for backward compatibility
def fill_pdf(
    input_pdf: str,
    output_pdf: str,
    data_dict: Dict[str, Union[str, bool, int]],
    flatten: bool = False,
) -> None:
    """
    Convenience function to fill PDF form in one call

    Args:
        input_pdf: Path to input PDF file
        output_pdf: Path for output PDF file
        data_dict: Dictionary with field data
        flatten: If True, remove form fields making the PDF static

    Raises:
        PDFFormFillerError: If any error occurs during process

    Example:
        >>> fill_pdf("form.pdf", "filled.pdf", {"name": "John"}, flatten=True)
    """
    filler = PDFFormFiller(input_pdf)
    filler.fill(data_dict)
    filler.save(output_pdf, flatten=flatten)
