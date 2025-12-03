"""
Pytest configuration and fixtures
"""
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test files

    Yields:
        Path to temporary directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def fixtures_dir() -> Path:
    """
    Get path to fixtures directory

    Returns:
        Path to test fixtures
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_pdf(fixtures_dir: Path) -> Path:
    """
    Get path to sample PDF form

    Returns:
        Path to sample PDF
    """
    sample = fixtures_dir / "sample_form.pdf"
    if not sample.exists():
        pytest.skip("Sample PDF not found")
    return sample


@pytest.fixture
def sample_data() -> dict:
    """
    Get sample form data for testing

    Returns:
        Dictionary with sample form data
    """
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": "30",
        "agree": True,
    }
