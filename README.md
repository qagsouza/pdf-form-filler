# PDF Form Filler

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Biblioteca Python para preenchimento automático de formulários PDF com suporte a campos de texto, checkboxes e radio buttons. Inclui interface de linha de comando (CLI) e aplicação web opcional com FastAPI + HTMX.

## Características

- ✅ Preenchimento de campos de texto, checkboxes e radio buttons
- ✅ Suporte a flatten (conversão para PDF estático)
- ✅ Interface de linha de comando (CLI)
- ✅ API REST com FastAPI (opcional)
- ✅ Interface web com HTMX (opcional)
- ✅ Type hints completos
- ✅ Validações de segurança
- ✅ Testes automatizados

## Instalação

### Instalação básica (biblioteca + CLI)

```bash
pip install -e .
```

### Com suporte web (FastAPI + HTMX)

```bash
pip install -e ".[web]"
```

### Para desenvolvimento

```bash
pip install -e ".[dev]"
```

### Instalação completa

```bash
pip install -e ".[all]"
```

## Uso

### Como biblioteca Python

```python
from pdf_form_filler import PDFFormFiller

# Criar instância
filler = PDFFormFiller("formulario.pdf")

# Listar campos disponíveis
campos = filler.get_available_fields()
print(campos)

# Preencher formulário
dados = {
    "nome": "João Silva",
    "email": "joao@exemplo.com",
    "idade": "30",
    "aceito_termos": True  # Checkbox
}
filler.fill(dados)

# Salvar (com flatten para tornar estático)
filler.save("formulario_preenchido.pdf", flatten=True)
```

### Função de conveniência

```python
from pdf_form_filler import fill_pdf

fill_pdf(
    "formulario.pdf",
    "preenchido.pdf",
    {"nome": "João", "aceito": True},
    flatten=True
)
```

### Interface de linha de comando (CLI)

#### Listar campos de um PDF

```bash
pdf-form-filler fields formulario.pdf
```

#### Preencher PDF com dados JSON

```bash
# Via string JSON
pdf-form-filler fill formulario.pdf preenchido.pdf \
    --data '{"nome": "João", "email": "joao@exemplo.com"}'

# Via arquivo JSON
pdf-form-filler fill formulario.pdf preenchido.pdf \
    --json-file dados.json
```

#### Listar campos durante preenchimento

```bash
pdf-form-filler fill formulario.pdf preenchido.pdf --list-fields
```

### Aplicação Web

#### Iniciar servidor

```bash
# Método 1: Usando uvicorn diretamente
uvicorn pdf_form_filler.web.app:app --reload

# Método 2: Via Python
python -m pdf_form_filler.web.app
```

#### Acessar interface

Abra o navegador em: http://127.0.0.1:8000

#### Endpoints da API REST

- `POST /api/extract` - Extrair campos de um PDF
- `POST /api/fill` - Preencher formulário via JSON
- `GET /health` - Health check

**Exemplo de uso da API:**

```bash
# Extrair campos
curl -X POST -F "pdf=@formulario.pdf" \
    http://localhost:8000/api/extract

# Preencher formulário
curl -X POST \
    -F "pdf_name=uploaded_file.pdf" \
    -F 'data={"nome": "João", "email": "joao@exemplo.com"}' \
    http://localhost:8000/api/fill
```

## Tipos de Campos Suportados

### Campos de texto (`/Tx`)
```python
filler.fill({"nome": "João Silva"})
```

### Checkboxes (`/Btn`)
```python
# Valores aceitos: True, False, "Yes", "No", "on", "off"
filler.fill({"aceito_termos": True})
```

### Radio buttons (`/Btn`)
```python
# Use o valor de exportação do campo
filler.fill({"genero": "Masculino"})
```

### Campos de escolha/dropdown (`/Ch`)
```python
filler.fill({"estado": "São Paulo"})
```

## Desenvolvimento

### Configurar ambiente

```bash
# Criar virtualenv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar em modo desenvolvimento
make install-dev
# ou
pip install -e ".[dev]"
```

### Executar testes

```bash
# Todos os testes
make test

# Com cobertura
make test-cov

# Apenas testes unitários
pytest tests/unit/

# Apenas testes de integração
pytest tests/integration/
```

### Formatação e linting

```bash
# Formatar código
make format

# Verificar formatação
make format-check

# Executar linter
make lint

# Corrigir problemas automaticamente
make lint-fix

# Verificar tipos
make type-check

# Verificar tudo
make check-all
```

### Comandos disponíveis

```bash
make help  # Ver todos os comandos
```

## Estrutura do Projeto

```
pdf-form-filler/
├── src/
│   └── pdf_form_filler/
│       ├── __init__.py          # API pública
│       ├── core.py              # Classe principal PDFFormFiller
│       ├── errors.py            # Exceções customizadas
│       ├── cli.py               # Interface de linha de comando
│       └── web/                 # Módulo web (opcional)
│           ├── __init__.py
│           ├── app.py           # Aplicação FastAPI
│           ├── templates/       # Templates HTML
│           └── static/          # Arquivos estáticos
├── tests/
│   ├── unit/                    # Testes unitários
│   ├── integration/             # Testes de integração
│   └── fixtures/                # PDFs de exemplo para testes
├── examples/                    # Exemplos de uso
├── pyproject.toml              # Configuração do projeto
├── setup.py                    # Setup (compatibilidade)
├── Makefile                    # Comandos de desenvolvimento
└── README.md
```

## Limitações

### Formatos suportados
- ✅ PDF com **AcroForm** (formulários padrão PDF)
- ❌ PDF com **XFA** (LiveCycle Designer) - não suportado

### Campos especiais
- Checkboxes/radio buttons: o valor deve corresponder ao "export value" do campo
- Alguns PDFs podem ter proteção que impede modificações

## Segurança

A aplicação web inclui validações de segurança:

- ✅ Validação de tipo MIME real (não apenas extensão)
- ✅ Limite de tamanho de upload (10MB padrão)
- ✅ Sanitização de nomes de arquivo (prevenção de path traversal)
- ✅ Verificação de magic bytes do PDF
- ⚠️ **Produção**: Configure CORS adequadamente em `web/app.py`
- ⚠️ **Produção**: Use HTTPS e autenticação apropriada

## Troubleshooting

### Checkbox não marca/desmarca

O valor para checkbox deve ser o "export value" do campo. Tente:
```python
filler.fill({"campo_checkbox": "Yes"})  # ou "Off", "On", etc.
```

### Campos não aparecem

Verifique se o PDF usa AcroForm:
```python
campos = filler.get_available_fields()
print(campos)  # Se vazio, pode não ser AcroForm
```

### PDF final está corrompido

- Certifique-se de que o PDF original não está protegido
- Tente sem flatten primeiro
- Verifique os logs/warnings

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/MinhaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. Push para a branch (`git push origin feature/MinhaFeature`)
5. Abra um Pull Request

### Diretrizes

- Adicione testes para novas funcionalidades
- Mantenha cobertura de testes > 80%
- Siga o style guide (black + ruff)
- Atualize a documentação

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Changelog

### v0.3.0 (atual)
- ✨ Arquitetura unificada (biblioteca + web)
- ✨ Melhor detecção de tipos de campos (pypdf + pdfrw)
- ✨ Validações de segurança
- ✨ Suporte a flatten
- ✨ Type hints completos
- ✨ Testes automatizados
- ✨ Configuração moderna (pyproject.toml)
- 📚 Documentação atualizada

### v0.2.0
- Interface web com FastAPI
- CLI com Click

### v0.1.0
- Versão inicial

## Créditos

Desenvolvido com:
- [pdfrw](https://github.com/pmaupin/pdfrw) - Manipulação de PDF
- [pypdf](https://github.com/py-pdf/pypdf) - Extração de campos
- [reportlab](https://www.reportlab.com/) - Geração de PDF
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web
- [Click](https://click.palletsprojects.com/) - Interface CLI

## Suporte

- 🐛 Reportar bugs: [Issues](https://github.com/seu-usuario/pdf-form-filler/issues)
- 💬 Discussões: [Discussions](https://github.com/seu-usuario/pdf-form-filler/discussions)
- 📧 Email: seu-email@exemplo.com
