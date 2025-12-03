"""
Unit tests for custom exceptions
"""
import pytest

from pdf_form_filler.errors import (
    PDFFormFillerError,
    PDFNotFoundError,
    PDFPermissionError,
    InvalidFieldError,
    PDFParseError,
    InvalidDataError,
)


def test_base_exception():
    """Test base exception"""
    exc = PDFFormFillerError("test error")
    assert str(exc) == "test error"
    assert isinstance(exc, Exception)


def test_pdf_not_found_error():
    """Test PDFNotFoundError"""
    exc = PDFNotFoundError("file not found")
    assert isinstance(exc, PDFFormFillerError)
    assert str(exc) == "file not found"


def test_pdf_permission_error():
    """Test PDFPermissionError"""
    exc = PDFPermissionError("permission denied")
    assert isinstance(exc, PDFFormFillerError)
    assert str(exc) == "permission denied"


def test_invalid_field_error():
    """Test InvalidFieldError"""
    exc = InvalidFieldError("field not found")
    assert isinstance(exc, PDFFormFillerError)
    assert str(exc) == "field not found"


def test_pdf_parse_error():
    """Test PDFParseError"""
    exc = PDFParseError("parse failed")
    assert isinstance(exc, PDFFormFillerError)
    assert str(exc) == "parse failed"


def test_invalid_data_error():
    """Test InvalidDataError"""
    exc = InvalidDataError("invalid data")
    assert isinstance(exc, PDFFormFillerError)
    assert str(exc) == "invalid data"
