"""
Core functionality for PDF Form Filler
"""
import os
import pdfrw
from .errors import (
    PDFNotFoundError, 
    PDFPermissionError, 
    PDFParseError, 
    InvalidDataError,
    InvalidFieldError
)


class PDFFormFiller:
    """
    Main class for filling PDF forms
    """
    
    def __init__(self, input_pdf):
        """
        Initialize PDF Form Filler with input PDF
        
        Args:
            input_pdf (str): Path to input PDF file
            
        Raises:
            PDFNotFoundError: If input PDF doesn't exist
            PDFParseError: If PDF cannot be parsed
            PDFPermissionError: If no read permission for PDF
        """
        self._validate_input_pdf(input_pdf)
        
        try:
            self.template_pdf = pdfrw.PdfReader(input_pdf)
            self.fields = self._extract_fields()
            self.input_pdf = input_pdf
        except pdfrw.PdfParseError as e:
            raise PDFParseError(f"Failed to parse PDF: {e}")
        except Exception as e:
            raise PDFFormFillerError(f"Unexpected error loading PDF: {e}")
    
    def _validate_input_pdf(self, input_pdf):
        """Validate input PDF file"""
        if not os.path.exists(input_pdf):
            raise PDFNotFoundError(f"PDF file not found: {input_pdf}")
        
        if not os.path.isfile(input_pdf):
            raise PDFNotFoundError(f"Path is not a file: {input_pdf}")
        
        if not os.access(input_pdf, os.R_OK):
            raise PDFPermissionError(f"No read permission for file: {input_pdf}")
    
    def _extract_fields(self):
        """Extract all form fields from PDF"""
        fields = {}
        
        for page_num, page in enumerate(self.template_pdf.pages):
            annotations = page['/Annots']
            if annotations:
                for annotation in annotations:
                    field = annotation.get('/T')
                    if field:
                        field_name = field[1:-1]  # Remove parentheses
                        fields[field_name] = {
                            'annotation': annotation,
                            'page': page_num,
                            'field_type': annotation.get('/FT', '/Tx')  # Default to text
                        }
        return fields
    
    def get_available_fields(self):
        """
        Get list of all available form fields
        
        Returns:
            list: List of field names
        """
        return list(self.fields.keys())
    
    def get_field_info(self, field_name):
        """
        Get detailed information about a specific field
        
        Args:
            field_name (str): Name of the field
            
        Returns:
            dict: Field information
            
        Raises:
            InvalidFieldError: If field doesn't exist
        """
        if field_name not in self.fields:
            raise InvalidFieldError(f"Field '{field_name}' not found in PDF")
        
        return self.fields[field_name]
    
    def fill(self, data):
        """
        Fill form with provided data
        
        Args:
            data (dict): Dictionary with field names as keys and values to fill
            
        Raises:
            InvalidDataError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise InvalidDataError("Data must be a dictionary")
        
        unused_fields = set(data.keys()) - set(self.fields.keys())
        if unused_fields:
            print(f"Warning: The following fields were not found in PDF: {list(unused_fields)}")
        
        for field_name, value in data.items():
            if field_name in self.fields:
                self._set_field_value(field_name, value)
    
    def _set_field_value(self, field_name, value):
        """Set value for a specific field"""
        field_info = self.fields[field_name]
        annotation = field_info['annotation']
        field_type = field_info['field_type']
        
        try:
            if field_type == '/Btn':  # Checkbox or radio button
                # For checkboxes, value should be boolean
                # For radio buttons, value should match option value
                if isinstance(value, bool):
                    if value:
                        annotation.update(pdfrw.PdfDict(
                            V=pdfrw.PdfName('Yes'),
                            AS=pdfrw.PdfName('Yes')
                        ))
                    else:
                        annotation.update(pdfrw.PdfDict(
                            V=pdfrw.PdfName('Off'),
                            AS=pdfrw.PdfName('Off')
                        ))
                else:
                    annotation.update(pdfrw.PdfDict(
                        V=pdfrw.PdfName(str(value)),
                        AS=pdfrw.PdfName(str(value))
                    ))
            else:  # Text fields and others
                annotation.update(pdfrw.PdfDict(V=str(value)))
                
        except Exception as e:
            print(f"Warning: Could not set value for field '{field_name}': {e}")
    
    def save(self, output_pdf):
        """
        Save filled PDF to output file
        
        Args:
            output_pdf (str): Path for output PDF file
            
        Raises:
            PDFPermissionError: If no write permission for output directory
        """
        output_dir = os.path.dirname(output_pdf) or '.'
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        if os.path.exists(output_pdf) and not os.access(output_pdf, os.W_OK):
            raise PDFPermissionError(f"No write permission for file: {output_pdf}")
        
        try:
            writer = pdfrw.PdfWriter()
            writer.write(output_pdf, self.template_pdf)
        except Exception as e:
            raise PDFFormFillerError(f"Failed to save PDF: {e}")


# Função de conveniência para compatibilidade com versão anterior
def fill_pdf(input_pdf, output_pdf, data_dict):
    """
    Convenience function to fill PDF form (backward compatibility)
    
    Args:
        input_pdf (str): Path to input PDF file
        output_pdf (str): Path for output PDF file
        data_dict (dict): Dictionary with field data
        
    Raises:
        PDFFormFillerError: If any error occurs during process
    """
    filler = PDFFormFiller(input_pdf)
    filler.fill(data_dict)
    filler.save(output_pdf)
