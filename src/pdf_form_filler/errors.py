"""
Custom exceptions for PDF Form Filler
"""

class PDFFormFillerError(Exception):
    """Base exception for PDF form filler operations"""
    pass

class PDFNotFoundError(PDFFormFillerError):
    """Raised when input PDF file is not found"""
    pass

class PDFPermissionError(PDFFormFillerError):
    """Raised when there's no permission to read/write PDF files"""
    pass

class InvalidFieldError(PDFFormFillerError):
    """Raised when trying to access invalid form fields"""
    pass

class PDFParseError(PDFFormFillerError):
    """Raised when PDF parsing fails"""
    pass

class InvalidDataError(PDFFormFillerError):
    """Raised when invalid data is provided for form filling"""
    pass
