# Configuração de Email

Este documento explica como configurar o sistema de notificações por email.

## Variáveis de Ambiente

Configure as seguintes variáveis de ambiente no arquivo `.env` ou no sistema:

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com           # Servidor SMTP
SMTP_PORT=587                      # Porta SMTP (587 para TLS, 465 para SSL)
SMTP_USER=seu-email@gmail.com      # Usuário SMTP
SMTP_PASSWORD=sua-senha-app        # Senha do SMTP
SMTP_FROM=seu-email@gmail.com      # Email remetente
SMTP_USE_TLS=true                  # Usar TLS
SMTP_USE_SSL=false                 # Usar SSL

# Application URL (para links nos emails)
APP_URL=http://localhost:8000
```

## Configuração para Gmail

Se você usar Gmail, será necessário gerar uma "Senha de App":

1. Acesse https://myaccount.google.com/security
2. Ative a verificação em duas etapas
3. Vá em "Senhas de app"
4. Selecione "Email" e "Outro (nome personalizado)"
5. Copie a senha gerada (16 caracteres)
6. Use essa senha no `SMTP_PASSWORD`

## Modo de Desenvolvimento (Console)

Para desenvolvimento, você pode usar o modo console que imprime os emails no terminal ao invés de enviar:

```bash
SMTP_HOST=console
```

## Providers Comuns

### Gmail
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### Outlook/Hotmail
```
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

### SendGrid
```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SUA_API_KEY
SMTP_USE_TLS=true
```

### Mailgun
```
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USE_TLS=true
```

## Uso

### No Formulário Web

1. Acesse um template e clique em "Preencher Formulário"
2. Marque a opção "Enviar PDF por email quando completado"
3. Preencha o email e nome do destinatário
4. Preencha o formulário normalmente
5. Ao submeter, o PDF será gerado e enviado por email

### Via API

```python
import requests

data = {
    "template_id": "template-uuid",
    "name": "Minha Requisição",
    "notes": "Observações",
    "data": {
        "campo1": "valor1",
        "campo2": "valor2"
    },
    "recipient_email": "destinatario@exemplo.com",
    "recipient_name": "Nome do Destinatário",
    "send_email": True
}

response = requests.post(
    "http://localhost:8000/api/requests",
    json=data,
    headers={"Authorization": f"Bearer {token}"}
)
```

## Templates de Email

Os templates de email estão em `src/pdf_form_filler/email_templates/`:

- `pdf_ready.html` - Template HTML para notificação de PDF pronto
- `pdf_ready.txt` - Template texto para notificação de PDF pronto

Você pode personalizar estes templates usando Jinja2.

### Variáveis Disponíveis

- `recipient_name` - Nome do destinatário
- `template_name` - Nome do template PDF
- `request_name` - Nome da requisição (opcional)
- `requester_name` - Nome de quem preencheu o formulário
- `notes` - Observações da requisição
- `pdf_filename` - Nome do arquivo PDF

## Verificando Emails Enviados

Na página de detalhes da requisição, você verá:

- ✉️ Email do destinatário
- Badge "Enviado" com timestamp quando o email foi enviado
- Badge "Pendente" se o email ainda não foi enviado

## Troubleshooting

### Email não está sendo enviado

1. Verifique as variáveis de ambiente
2. Teste a conexão SMTP:
   ```python
   from src.pdf_form_filler.services.email_service import EmailService
   
   service = EmailService()
   service.test_connection()  # Deve retornar True
   ```

3. Verifique os logs do servidor

### Erro de autenticação

- Gmail: Use senha de app, não sua senha normal
- Verifique se o usuário e senha estão corretos
- Verifique se a porta está correta (587 para TLS)

### Email cai no spam

- Configure SPF, DKIM e DMARC no seu domínio
- Use um serviço de email profissional (SendGrid, Mailgun, etc.)
- Evite palavras que acionam filtros de spam

## Segurança

- **NUNCA** commite senhas no código
- Use variáveis de ambiente ou um gerenciador de secrets
- Em produção, use serviços de email profissionais
- Implemente rate limiting para evitar abuso
- Valide emails antes de enviar

## Migração do Banco de Dados

O campo `email_sent` foi adicionado à tabela `request_instances`. Execute a migração:

```bash
alembic upgrade head
```

## Status do Email

O sistema rastreia o status do envio:

- `email_sent`: NULL - Email não foi enviado
- `email_sent`: TIMESTAMP - Email enviado com sucesso neste horário
- `status`: "sent" - Requisição completada e email enviado
