"""
FastAPI web application for PDF Form Filler with HTMX interface
"""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Dict, Optional

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from ..core import PDFFormFiller
from ..errors import PDFFormFillerError
from ..database import init_db
from ..api import auth as api_auth, templates as api_templates, requests as api_requests
from .routes import auth, dashboard, admin, requests as requests_routes
from .routes import templates as templates_routes, profile


# Configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf"}
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Get templates and static directories
MODULE_DIR = Path(__file__).parent
TEMPLATES_DIR = MODULE_DIR / "templates"
STATIC_DIR = MODULE_DIR / "static"


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="PDF Form Filler",
        description="Automatic PDF form filling with HTMX interface",
        version="0.3.0",
    )

    # Initialize database
    init_db()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_auth.router)
    app.include_router(api_templates.router)
    app.include_router(api_requests.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(admin.router)
    app.include_router(templates_routes.router)
    app.include_router(requests_routes.router)
    app.include_router(profile.router)

    # Mount static files if directory exists
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Setup templates
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    def validate_pdf_file(filename: str, content: bytes) -> None:
        """
        Validate uploaded PDF file

        Args:
            filename: Name of the file
            content: File content

        Raises:
            HTTPException: If validation fails
        """
        # Check extension
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Check size
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / 1024 / 1024}MB",
            )

        # Check MIME type (magic bytes)
        if not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Get only the basename (remove any path components)
        safe_name = os.path.basename(filename)

        # Generate unique filename with UUID prefix
        return f"{uuid.uuid4().hex}_{safe_name}"

    @app.post("/upload", response_class=HTMLResponse)
    async def upload_pdf(request: Request, pdf: UploadFile = File(...)):
        """
        Handle PDF upload and return form fields as HTML fragment (HTMX)

        Args:
            request: FastAPI request
            pdf: Uploaded PDF file

        Returns:
            HTML fragment with form fields
        """
        try:
            # Read file content
            content = await pdf.read()

            # Validate file
            validate_pdf_file(pdf.filename or "file.pdf", content)

            # Save file with sanitized name
            filename = sanitize_filename(pdf.filename or "file.pdf")
            path = UPLOAD_DIR / filename

            with open(path, "wb") as f:
                f.write(content)

            # Extract fields using unified library
            filler = PDFFormFiller(str(path))
            fields_list = filler.get_available_fields()

            # Build fields dictionary with type information
            fields = {}
            for field_name in fields_list:
                field_info = filler.get_field_info(field_name)
                fields[field_name] = {
                    "type": field_info.get("type", "text"),
                    "value": field_info.get("value", ""),
                }

            return templates.TemplateResponse(
                request,
                "fill_fields.html",
                {"fields": fields, "pdf_name": filename},
            )

        except HTTPException:
            raise  # Re-raise HTTPException from validation
        except PDFFormFillerError as e:
            raise HTTPException(status_code=400, detail=f"PDF error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    @app.post("/fill", response_class=HTMLResponse)
    async def fill_form(request: Request, pdf_name: str = Form(...)):
        """
        Receive filled values and produce filled PDF

        Args:
            request: FastAPI request
            pdf_name: Name of the uploaded PDF

        Returns:
            HTML fragment with download link
        """
        try:
            # Validate pdf_name to prevent path traversal
            safe_pdf_name = os.path.basename(pdf_name)
            input_path = UPLOAD_DIR / safe_pdf_name

            if not input_path.exists():
                raise HTTPException(status_code=404, detail="PDF file not found")

            # Parse form data
            form = await request.form()
            data = {}

            for key, val in form.multi_items():
                if key == "pdf_name":
                    continue

                # Handle checkboxes (HTML sends 'on' when checked)
                if val == "on":
                    data[key] = True
                elif isinstance(val, list):
                    data[key] = val
                else:
                    # Only add if not empty
                    if val and val.strip():
                        data[key] = val

            # Fill PDF using unified library
            out_name = f"filled_{uuid.uuid4().hex}_{safe_pdf_name}"
            out_path = UPLOAD_DIR / out_name

            filler = PDFFormFiller(str(input_path))
            filler.fill(data)
            filler.save(str(out_path), flatten=True)

            return templates.TemplateResponse(
                request,
                "download_fragment.html",
                {"file_url": f"/download/{out_name}"},
            )

        except HTTPException:
            raise  # Re-raise HTTPException from validation
        except PDFFormFillerError as e:
            raise HTTPException(status_code=400, detail=f"PDF error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    @app.get("/download/{fname}")
    async def download_file(fname: str):
        """
        Download filled PDF

        Args:
            fname: Filename to download

        Returns:
            PDF file response
        """
        # Sanitize filename to prevent path traversal
        safe_fname = os.path.basename(fname)
        path = UPLOAD_DIR / safe_fname

        if not path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Verify it's a PDF
        if not safe_fname.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Invalid file type")

        return FileResponse(
            path, filename=safe_fname, media_type="application/pdf"
        )

    # REST API endpoints

    @app.post("/api/extract")
    async def api_extract(pdf: UploadFile = File(...)):
        """
        Extract form fields from PDF (REST API)

        Args:
            pdf: Uploaded PDF file

        Returns:
            JSON with field information
        """
        try:
            # Read and validate
            content = await pdf.read()
            validate_pdf_file(pdf.filename or "file.pdf", content)

            # Save temporarily
            filename = sanitize_filename(pdf.filename or "file.pdf")
            path = UPLOAD_DIR / filename

            with open(path, "wb") as f:
                f.write(content)

            # Extract fields
            filler = PDFFormFiller(str(path))
            fields_list = filler.get_available_fields()

            fields = {}
            for field_name in fields_list:
                field_info = filler.get_field_info(field_name)
                fields[field_name] = {
                    "type": field_info.get("type", "text"),
                    "value": field_info.get("value", ""),
                }

            return JSONResponse({"filename": filename, "fields": fields})

        except HTTPException:
            raise  # Re-raise HTTPException from validation
        except PDFFormFillerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/fill")
    async def api_fill(
        pdf_name: str = Form(...),
        data: Optional[str] = Form(None),
    ):
        """
        Fill PDF form (REST API)

        Args:
            pdf_name: Name of uploaded PDF
            data: JSON string with field data

        Returns:
            JSON with download URL
        """
        try:
            import json

            # Validate and parse
            safe_pdf_name = os.path.basename(pdf_name)
            input_path = UPLOAD_DIR / safe_pdf_name

            if not input_path.exists():
                raise HTTPException(status_code=404, detail="PDF file not found")

            if not data:
                raise HTTPException(status_code=400, detail="No data provided")

            form_data = json.loads(data)

            # Fill PDF
            out_name = f"filled_{uuid.uuid4().hex}_{safe_pdf_name}"
            out_path = UPLOAD_DIR / out_name

            filler = PDFFormFiller(str(input_path))
            filler.fill(form_data)
            filler.save(str(out_path), flatten=True)

            return JSONResponse(
                {"success": True, "download_url": f"/download/{out_name}"}
            )

        except HTTPException:
            raise  # Re-raise HTTPException from validation
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
        except PDFFormFillerError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "ok"}

    return app


# Create default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
