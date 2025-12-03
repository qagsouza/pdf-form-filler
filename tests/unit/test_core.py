"""
Unit tests for core PDFFormFiller class
"""
import pytest
from pathlib import Path

from pdf_form_filler.core import PDFFormFiller, fill_pdf
from pdf_form_filler.errors import (
    PDFNotFoundError,
    PDFPermissionError,
    InvalidDataError,
    InvalidFieldError,
)


class TestPDFFormFillerInit:
    """Tests for PDFFormFiller initialization"""

    def test_init_with_nonexistent_file(self):
        """Test initialization with non-existent PDF"""
        with pytest.raises(PDFNotFoundError):
            PDFFormFiller("nonexistent.pdf")

    def test_init_with_directory(self, temp_dir: Path):
        """Test initialization with directory instead of file"""
        with pytest.raises(PDFNotFoundError):
            PDFFormFiller(str(temp_dir))

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_init_with_valid_pdf(self, sample_pdf: Path):
        """Test initialization with valid PDF"""
        filler = PDFFormFiller(str(sample_pdf))
        assert filler.input_pdf == str(sample_pdf)
        assert filler.template_pdf is not None
        assert isinstance(filler.fields, dict)


class TestFieldExtraction:
    """Tests for field extraction"""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_get_available_fields(self, sample_pdf: Path):
        """Test getting list of available fields"""
        filler = PDFFormFiller(str(sample_pdf))
        fields = filler.get_available_fields()
        assert isinstance(fields, list)

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_get_field_info_invalid(self, sample_pdf: Path):
        """Test getting info for non-existent field"""
        filler = PDFFormFiller(str(sample_pdf))
        with pytest.raises(InvalidFieldError):
            filler.get_field_info("nonexistent_field")

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_get_field_type(self, sample_pdf: Path):
        """Test getting field type"""
        filler = PDFFormFiller(str(sample_pdf))
        fields = filler.get_available_fields()
        if fields:
            field_type = filler.get_field_type(fields[0])
            assert field_type in ["text", "button", "choice", "unknown"]


class TestFormFilling:
    """Tests for form filling"""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_fill_with_invalid_data(self, sample_pdf: Path):
        """Test filling with invalid data type"""
        filler = PDFFormFiller(str(sample_pdf))
        with pytest.raises(InvalidDataError):
            filler.fill("not a dict")

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_fill_with_empty_data(self, sample_pdf: Path):
        """Test filling with empty data"""
        filler = PDFFormFiller(str(sample_pdf))
        filler.fill({})  # Should not raise

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_fill_with_valid_data(self, sample_pdf: Path, sample_data: dict):
        """Test filling with valid data"""
        filler = PDFFormFiller(str(sample_pdf))
        filler.fill(sample_data)  # Should not raise


class TestSaving:
    """Tests for saving PDFs"""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_save_to_temp_dir(
        self, sample_pdf: Path, temp_dir: Path, sample_data: dict
    ):
        """Test saving filled PDF to temporary directory"""
        filler = PDFFormFiller(str(sample_pdf))
        filler.fill(sample_data)

        output_path = temp_dir / "output.pdf"
        filler.save(str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_save_with_flatten(
        self, sample_pdf: Path, temp_dir: Path, sample_data: dict
    ):
        """Test saving with flatten option"""
        filler = PDFFormFiller(str(sample_pdf))
        filler.fill(sample_data)

        output_path = temp_dir / "flattened.pdf"
        filler.save(str(output_path), flatten=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestConvenienceFunction:
    """Tests for fill_pdf convenience function"""

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample_form.pdf").exists(),
        reason="Sample PDF not found",
    )
    def test_fill_pdf_function(
        self, sample_pdf: Path, temp_dir: Path, sample_data: dict
    ):
        """Test fill_pdf convenience function"""
        output_path = temp_dir / "filled.pdf"

        fill_pdf(str(sample_pdf), str(output_path), sample_data, flatten=True)

        assert output_path.exists()
        assert output_path.stat().st_size > 0
