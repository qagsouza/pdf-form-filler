# PDF Form Filler (FastAPI + HTMX)

Projeto exemplo em Python que:
- Recebe upload de um PDF com campos (AcroForm)
- Detecta campos de texto, checkbox e radio
- Exibe formulário web (HTMX) para preenchimento
- Gera PDF preenchido e faz *flatten* automaticamente
- Fornece API REST para integração
- Server: FastAPI + Uvicorn

## Como usar (local)
1. Crie e ative um virtualenv (recomendado)
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode o servidor:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Abra `http://127.0.0.1:8000/`

## Arquivos importantes
- `app/main.py` - FastAPI application (endpoints web + API)
- `app/pdf_utils.py` - utilitários para extrair e preencher campos (pdfrw + reportlab)
- `templates/` - Jinja2 templates utilizados pelo HTMX
- `uploads/` - local onde PDFs submetidos e gerados ficam armazenados (criado automaticamente)

## Observações
- Funciona para PDFs com **AcroForm**. PDFs XFA (LiveCycle) não são suportados.
- Checkbox/radio são tratados via PDFrw: o valor esperado para *checkbox/radio* é a *export value* do campo (ex: "Yes").
- Flatten remove os campos de formulário tornando o resultado final um PDF estático.

# pdf-form-filler
