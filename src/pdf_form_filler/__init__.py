"""
PDF Form Filler - Automatically fill PDF forms with Python
"""

__version__ = "0.2.0"

from .core import PDFFormFiller, fill_pdf
from .errors import PDFFormFillerError

__all__ = ['PDFFormFiller', 'fill_pdf', 'PDFFormFillerError']
