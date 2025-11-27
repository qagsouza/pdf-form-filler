import os
import uuid
from fastapi import FastAPI, Request, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from typing import Dict
from .pdf_utils import extract_fields, fill_pdf

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.mount('/static', StaticFiles(directory=os.path.join(BASE_DIR, 'static')), name='static')
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, 'app', 'templates'))

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    """Serve the upload page."""
    return templates.TemplateResponse('upload.html', {'request': request})

@app.post('/upload', response_class=HTMLResponse)
async def upload_pdf(request: Request, pdf: UploadFile = File(...)):
    """Handle PDF upload. Returns an HTML fragment with the generated form (HTMX)."""
    filename = f"{uuid.uuid4().hex}_{pdf.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, 'wb') as f:
        content = await pdf.read()
        f.write(content)
    fields = extract_fields(path)
    # Render fragment (form) for HTMX to inject
    return templates.TemplateResponse('fill_fields.html', {'request': request, 'fields': fields, 'pdf_name': filename})

@app.post('/fill', response_class=HTMLResponse)
async def fill_form(request: Request, pdf_name: str = Form(...)):
    """Receive filled values from form and produce filled PDF. Returns a download link fragment."""
    form = await request.form()
    data = {}
    for key, val in form.multi_items():
        if key == 'pdf_name':
            continue
        # Checkboxes: HTML sends 'on' when checked; for unchecked they are absent.
        # For group of checkboxes with same name we might have multiple values; handle lists.
        if isinstance(val, list):
            data[key] = val
        else:
            data[key] = val
    input_path = os.path.join(UPLOAD_DIR, pdf_name)
    out_name = f"filled_{uuid.uuid4().hex}_{pdf_name}"
    out_path = os.path.join(UPLOAD_DIR, out_name)
    fill_pdf(input_path, out_path, data, flatten=True)
    return templates.TemplateResponse('download_fragment.html', {'request': request, 'file_url': f'/download/{out_name}'})

@app.get('/download/{fname}')
def download_file(fname: str):
    path = os.path.join(UPLOAD_DIR, fname)
    if not os.path.exists(path):
        return JSONResponse({'error': 'file not found'}, status_code=404)
    return FileResponse(path, filename=fname, media_type='application/pdf')

# REST API endpoints
@app.post('/api/extract')
async def api_extract(pdf: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{pdf.filename}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, 'wb') as f:
        f.write(await pdf.read())
    fields = extract_fields(path)
    return JSONResponse(fields)

@app.post('/api/fill')
async def api_fill(payload: Dict[str, str] = Depends(lambda: {})):
    # For simplicity, this endpoint expects JSON body with keys:
    # { "pdf_path": "<server-side path or uploaded filename>", "data": { field: value, ... } }
    # In a production scenario you would implement upload + fill or accept base64 PDF.
    return JSONResponse({'detail': 'Implement client-specific flow; use /upload + /fill or extend this endpoint.'})
