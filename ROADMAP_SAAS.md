# Roadmap - PDF Form Filler SaaS

## 🎯 Visão do Produto

Sistema multi-usuário para gerenciamento e preenchimento colaborativo de formulários PDF.

### Casos de Uso
- **RH:** Formulários de admissão, férias, reembolsos
- **Educação:** Formulários acadêmicos compartilhados entre departamentos
- **Empresas:** Solicitações de compras, requisições internas
- **Governo:** Formulários públicos reutilizáveis

---

## 📋 Funcionalidades Planejadas

### 1. Autenticação e Autorização
**Status:** 🔴 Não Implementado

#### Requisitos
- [ ] Sistema de registro e login
- [ ] Autenticação JWT ou sessão
- [ ] Perfis de usuário
- [ ] Recuperação de senha
- [ ] Confirmação de email

#### Tecnologias Sugeridas
- **FastAPI Users** - Framework completo de autenticação
- **Passlib** - Hashing de senhas
- **python-jose** - JWT tokens
- **SQLAlchemy** - ORM para gerenciar usuários

#### Estrutura de Dados
```python
User:
  - id: UUID
  - email: str (unique)
  - full_name: str
  - hashed_password: str
  - is_active: bool
  - is_verified: bool
  - created_at: datetime
  - updated_at: datetime
```

---

### 2. Gerenciamento de Templates PDF
**Status:** 🔴 Não Implementado

#### Requisitos
- [ ] Upload de PDFs como templates
- [ ] Listar templates do usuário
- [ ] Editar metadados do template
- [ ] Deletar templates
- [ ] Compartilhamento de templates entre usuários
- [ ] Permissões (owner, editor, viewer)
- [ ] Versionamento de templates

#### Estrutura de Dados
```python
Template:
  - id: UUID
  - name: str
  - description: str
  - owner_id: UUID (FK -> User)
  - file_path: str
  - fields_metadata: JSON  # Campos detectados
  - created_at: datetime
  - updated_at: datetime
  - version: int

TemplateShare:
  - id: UUID
  - template_id: UUID (FK -> Template)
  - user_id: UUID (FK -> User)
  - permission: enum (viewer, editor, admin)
  - shared_by: UUID (FK -> User)
  - created_at: datetime
```

#### Endpoints
```
POST   /api/templates                    # Upload template
GET    /api/templates                    # Listar meus templates
GET    /api/templates/shared             # Templates compartilhados comigo
GET    /api/templates/{id}               # Detalhes do template
PUT    /api/templates/{id}               # Atualizar metadados
DELETE /api/templates/{id}               # Deletar template
POST   /api/templates/{id}/share         # Compartilhar com usuário
DELETE /api/templates/{id}/share/{user}  # Remover compartilhamento
GET    /api/templates/{id}/fields        # Listar campos
```

---

### 3. Sistema de Requisições
**Status:** 🔴 Não Implementado

#### Requisitos
- [ ] Criar requisição de preenchimento (única ou batch)
- [ ] Listar minhas requisições
- [ ] Visualizar status da requisição
- [ ] Cancelar requisição pendente
- [ ] Histórico de requisições

#### Estrutura de Dados
```python
Request:
  - id: UUID
  - template_id: UUID (FK -> Template)
  - requester_id: UUID (FK -> User)
  - type: enum (single, batch)
  - status: enum (pending, processing, completed, failed)
  - created_at: datetime
  - completed_at: datetime

RequestInstance:
  - id: UUID
  - request_id: UUID (FK -> Request)
  - data: JSON  # Dados para preencher
  - recipient_email: str (nullable)
  - status: enum (pending, processing, completed, failed, sent)
  - filled_pdf_path: str (nullable)
  - error_message: str (nullable)
  - created_at: datetime
  - processed_at: datetime
```

#### Endpoints
```
POST   /api/requests                     # Criar requisição
GET    /api/requests                     # Listar requisições
GET    /api/requests/{id}                # Detalhes da requisição
DELETE /api/requests/{id}                # Cancelar requisição
GET    /api/requests/{id}/instances      # Listar instâncias
GET    /api/requests/{id}/download-all   # Download ZIP com todos
```

---

### 4. Processamento em Batch
**Status:** 🔴 Não Implementado

#### Requisitos
- [ ] Aceitar CSV/JSON com múltiplos registros
- [ ] Processar assincronamente
- [ ] Fila de processamento (Celery ou RQ)
- [ ] Progress tracking
- [ ] Notificação quando concluído

#### Tecnologias Sugeridas
- **Celery** + **Redis** - Fila de tarefas distribuída
- **RQ (Redis Queue)** - Alternativa mais simples
- **Dramatiq** - Moderna e leve

#### Formato de Entrada (CSV)
```csv
nome,email,departamento,enviar_email
João Silva,joao@empresa.com,TI,sim
Maria Santos,maria@empresa.com,RH,sim
```

#### Formato de Entrada (JSON)
```json
{
  "template_id": "uuid",
  "instances": [
    {
      "data": {"nome": "João", "email": "joao@empresa.com"},
      "recipient_email": "joao@empresa.com"
    },
    {
      "data": {"nome": "Maria", "email": "maria@empresa.com"},
      "recipient_email": "maria@empresa.com"
    }
  ]
}
```

#### Endpoints
```
POST   /api/requests/batch               # Upload CSV/JSON
GET    /api/requests/{id}/progress       # Progress da requisição batch
```

---

### 5. Sistema de Email
**Status:** 🔴 Não Implementado

#### Requisitos
- [ ] Envio de PDF por email
- [ ] Templates de email customizáveis
- [ ] Fila de envio
- [ ] Logs de envio
- [ ] Retry em caso de falha

#### Tecnologias Sugeridas
- **FastAPI-Mail** - Integração com FastAPI
- **python-dotenv** - Configurações de SMTP
- **Jinja2** - Templates de email

#### Estrutura de Dados
```python
EmailLog:
  - id: UUID
  - request_instance_id: UUID (FK -> RequestInstance)
  - recipient: str
  - subject: str
  - status: enum (pending, sent, failed)
  - error_message: str (nullable)
  - sent_at: datetime
  - attempts: int
```

#### Configurações
```python
SMTP_HOST: str
SMTP_PORT: int
SMTP_USER: str
SMTP_PASSWORD: str
SMTP_FROM: str
EMAIL_TEMPLATES_DIR: str
```

---

### 6. Storage de Arquivos
**Status:** 🟡 Parcialmente Implementado (local apenas)

#### Requisitos Atuais
- [x] Storage local básico em `uploads/`

#### Melhorias Necessárias
- [ ] Organização por usuário e template
- [ ] Cleanup automático de arquivos antigos
- [ ] Suporte a S3/MinIO para produção
- [ ] CDN para downloads
- [ ] Compressão de PDFs

#### Estrutura Proposta
```
storage/
├── templates/
│   └── {user_id}/
│       └── {template_id}/
│           └── template.pdf
├── filled/
│   └── {user_id}/
│       └── {request_id}/
│           └── {instance_id}.pdf
└── temp/
    └── {upload_session}/
```

#### Tecnologias Sugeridas
- **boto3** - Cliente AWS S3
- **minio** - S3-compatible open source
- **FastAPI FileSystem** - Abstração de storage

---

### 7. Dashboard Web
**Status:** 🟡 Interface básica existe

#### Páginas Necessárias

**Públicas:**
- [ ] Landing page
- [ ] Login / Registro
- [ ] Recuperação de senha

**Autenticadas:**
- [ ] Dashboard principal
  - Resumo de templates
  - Requisições recentes
  - Estatísticas
- [ ] Gerenciar Templates
  - Listar templates
  - Upload novo template
  - Editar/Deletar
  - Compartilhar
- [ ] Nova Requisição
  - Escolher template
  - Modo single/batch
  - Preencher dados ou upload CSV
  - Configurar envio de email
- [ ] Minhas Requisições
  - Listar com filtros
  - Ver detalhes
  - Download individual/ZIP
- [ ] Configurações
  - Perfil do usuário
  - Preferências de email
  - API keys

#### Tecnologias Sugeridas (Frontend)
- **HTMX** - Interatividade sem JavaScript complexo
- **Alpine.js** - JavaScript reativo leve
- **TailwindCSS** - Framework CSS moderno
- **OU React/Vue** - Para SPA completa

---

### 8. API REST Completa
**Status:** 🟡 Parcialmente Implementado

#### Endpoints Necessários

**Autenticação:**
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/me
PUT    /api/auth/me
```

**Templates:**
```
[Já documentado acima]
```

**Requisições:**
```
[Já documentado acima]
```

**Estatísticas:**
```
GET    /api/stats/dashboard
GET    /api/stats/templates/{id}
GET    /api/stats/usage
```

---

## 🏗️ Arquitetura Proposta

### Stack Tecnológica

#### Backend
- **FastAPI** - Framework web (já está)
- **SQLAlchemy** - ORM
- **Alembic** - Migrações de banco
- **PostgreSQL** - Banco de dados principal
- **Redis** - Cache e fila
- **Celery** - Tarefas assíncronas
- **FastAPI-Users** - Autenticação

#### Frontend
- **Jinja2** - Templates (já está)
- **HTMX/Alpine.js** - Interatividade
- **TailwindCSS** - Estilos

#### Infraestrutura
- **Docker** - Containerização
- **Docker Compose** - Desenvolvimento local
- **Nginx** - Proxy reverso
- **MinIO/S3** - Storage de arquivos

### Estrutura de Diretórios Proposta

```
pdf-form-filler/
├── src/
│   └── pdf_form_filler/
│       ├── __init__.py
│       ├── core.py              # Lógica de PDF (já existe)
│       ├── config.py            # NOVO: Configurações
│       ├── database.py          # NOVO: Setup DB
│       ├── dependencies.py      # NOVO: FastAPI dependencies
│       │
│       ├── models/              # NOVO: SQLAlchemy models
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── template.py
│       │   ├── request.py
│       │   └── email_log.py
│       │
│       ├── schemas/             # NOVO: Pydantic schemas
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── template.py
│       │   └── request.py
│       │
│       ├── services/            # NOVO: Lógica de negócio
│       │   ├── __init__.py
│       │   ├── template_service.py
│       │   ├── request_service.py
│       │   ├── email_service.py
│       │   └── storage_service.py
│       │
│       ├── api/                 # NOVO: Rotas da API
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── templates.py
│       │   ├── requests.py
│       │   └── stats.py
│       │
│       ├── web/                 # Web UI (já existe, expandir)
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── routes/          # NOVO: Rotas web
│       │   │   ├── __init__.py
│       │   │   ├── auth.py
│       │   │   ├── dashboard.py
│       │   │   └── templates.py
│       │   ├── templates/
│       │   └── static/
│       │
│       ├── tasks/               # NOVO: Celery tasks
│       │   ├── __init__.py
│       │   ├── fill_pdf.py
│       │   └── send_email.py
│       │
│       └── utils/               # NOVO: Utilitários
│           ├── __init__.py
│           ├── auth.py
│           ├── storage.py
│           └── email.py
│
├── alembic/                     # NOVO: Migrações
│   ├── versions/
│   └── env.py
│
├── docker/                      # NOVO: Docker configs
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/                     # NOVO: Testes E2E
│
└── docs/                        # NOVO: Documentação
    ├── api.md
    ├── deployment.md
    └── user_guide.md
```

---

## 🎯 Plano de Implementação

### Fase 1: Fundação (2-3 semanas)
**Objetivo:** Infraestrutura base e autenticação

- [ ] Setup PostgreSQL e SQLAlchemy
- [ ] Modelos de User
- [ ] Alembic migrations
- [ ] FastAPI-Users integração
- [ ] Login/Registro UI
- [ ] Testes de autenticação

**Entregável:** Sistema com login funcional

---

### Fase 2: Gestão de Templates (2 semanas)
**Objetivo:** CRUD de templates com compartilhamento

- [ ] Modelo Template e TemplateShare
- [ ] Endpoints de API para templates
- [ ] UI para gerenciar templates
- [ ] Sistema de permissões
- [ ] Storage organizado por usuário
- [ ] Testes

**Entregável:** Usuários podem fazer upload e compartilhar templates

---

### Fase 3: Requisições Simples (2 semanas)
**Objetivo:** Preenchimento individual

- [ ] Modelo Request e RequestInstance
- [ ] API para criar requisição single
- [ ] UI para preencher formulário
- [ ] Processamento síncrono
- [ ] Download do PDF
- [ ] Testes

**Entregável:** Usuários podem preencher um formulário por vez

---

### Fase 4: Processamento Assíncrono (2 semanas)
**Objetivo:** Batch e filas

- [ ] Setup Celery + Redis
- [ ] Task para processar PDF
- [ ] Upload de CSV/JSON
- [ ] Progress tracking
- [ ] UI para acompanhar progresso
- [ ] Testes

**Entregável:** Usuários podem submeter múltiplas requisições

---

### Fase 5: Sistema de Email (1-2 semanas)
**Objetivo:** Envio automático

- [ ] Setup SMTP
- [ ] Templates de email
- [ ] Task Celery para envio
- [ ] Logs de email
- [ ] UI para configurar destinatários
- [ ] Testes

**Entregável:** PDFs são enviados por email automaticamente

---

### Fase 6: Dashboard e Polimento (2 semanas)
**Objetivo:** UX completo

- [ ] Dashboard com estatísticas
- [ ] Filtros e busca
- [ ] Download em ZIP
- [ ] Notificações
- [ ] Documentação de API
- [ ] Testes E2E

**Entregável:** Sistema completo e polido

---

### Fase 7: Deploy e Produção (1-2 semanas)
**Objetivo:** Sistema em produção

- [ ] Dockerização completa
- [ ] CI/CD com GitHub Actions
- [ ] Deploy em cloud (Railway/Fly.io/AWS)
- [ ] Monitoramento (Sentry)
- [ ] Backups automatizados
- [ ] Documentação de deploy

**Entregável:** Sistema rodando em produção

---

## 📊 Estimativa Total

**Tempo:** 12-15 semanas (3-4 meses)
**Complexidade:** Alta
**Desenvolvedor:** 1 full-stack

---

## 🚀 Quick Start para Fase 1

### 1. Instalar Dependências Extras

```bash
pip install \
  sqlalchemy \
  alembic \
  psycopg2-binary \
  fastapi-users[sqlalchemy] \
  python-jose[cryptography] \
  passlib[bcrypt] \
  redis \
  celery
```

### 2. Criar Database Models

```python
# src/pdf_form_filler/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3. Setup Alembic

```bash
alembic init alembic
alembic revision --autogenerate -m "Create users table"
alembic upgrade head
```

---

## 💡 Decisões Arquiteturais

### Por que PostgreSQL?
- Relacionamentos complexos (users, templates, shares, requests)
- ACID compliance
- JSON fields para metadados flexíveis
- Excelente suporte no ecossistema Python

### Por que Celery?
- Processamento batch pode demorar
- Envio de emails deve ser assíncrono
- Escalável horizontalmente

### Por que FastAPI-Users?
- Implementação pronta de autenticação
- JWT + Cookie sessions
- Reset de senha out-of-the-box
- Reduz 70% do código de auth

### Storage: Local vs S3?
- **Desenvolvimento:** Local (mais simples)
- **Produção:** S3/MinIO (escalável, confiável)
- Usar abstração para trocar facilmente

---

## 📝 Próximos Passos Imediatos

1. **Decidir stack de deploy:**
   - Self-hosted (VPS + Docker)
   - Cloud (AWS/GCP/Azure)
   - PaaS (Railway/Fly.io/Render)

2. **Escolher frontend approach:**
   - HTMX + Alpine (mais simples)
   - React/Vue SPA (mais moderno)

3. **Definir modelo de negócio:**
   - Free tier?
   - Limites por usuário?
   - Pricing plans?

4. **Começar Fase 1:**
   - Setup PostgreSQL
   - Implementar autenticação
   - UI de login/registro

---

## 🤝 Contribuição

Este roadmap é um documento vivo. Ajustes serão feitos conforme:
- Feedback de usuários
- Limitações técnicas descobertas
- Mudanças de prioridade

**Quer começar?** Vamos implementar a Fase 1 juntos!
