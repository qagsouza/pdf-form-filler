# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.3.0] - 2024-12-02

### Adicionado
- Arquitetura unificada com biblioteca core e módulo web separado
- Detecção aprimorada de tipos de campos usando pypdf + pdfrw
- Suporte completo a flatten (conversão para PDF estático)
- Type hints completos em toda a codebase
- Validações de segurança (MIME type, tamanho, path traversal)
- Estrutura completa de testes (unitários e integração)
- Configuração moderna com pyproject.toml
- EditorConfig para consistência de estilo
- Makefile com comandos de desenvolvimento
- Arquivo py.typed para suporte a type checking
- Método `get_field_type()` para obter tipo de campo específico
- Método `_flatten_form()` para remover campos de formulário
- Health check endpoint na API web

### Alterado
- Movido módulo web para `src/pdf_form_filler/web/`
- Melhorada extração de campos com fallback entre pypdf e pdfrw
- Refatorado `core.py` com melhor organização e documentação
- Atualizado `__init__.py` para versão 0.3.0
- Simplificado `setup.py` para usar apenas pyproject.toml
- Expandido `.gitignore` com novos artefatos de build e cache

### Corrigido
- Tratamento de diferentes tipos de campos (text, button, choice)
- Validação de permissões de arquivo
- Sanitização de nomes de arquivo para prevenir path traversal

### Segurança
- Adicionada validação de magic bytes do PDF
- Implementado limite de tamanho de upload (10MB)
- Sanitização de nomes de arquivo
- Validação de tipo MIME real

## [0.2.0] - 2024-11-26

### Adicionado
- Interface web com FastAPI e HTMX
- Templates HTML para upload e preenchimento
- Endpoints REST API
- Suporte a arquivos estáticos
- Diretório de uploads

### Alterado
- Estrutura do projeto organizada em `app/`

## [0.1.0] - Data inicial

### Adicionado
- Classe base `PDFFormFiller`
- Suporte a campos de texto e checkboxes
- Interface CLI básica com Click
- Função de conveniência `fill_pdf()`
- Tratamento de erros com exceções customizadas

[0.3.0]: https://github.com/seu-usuario/pdf-form-filler/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/seu-usuario/pdf-form-filler/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/seu-usuario/pdf-form-filler/releases/tag/v0.1.0
