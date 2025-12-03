"""
Email service for sending emails with attachment support
"""
import logging
import os
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails with attachment support"""

    def __init__(self):
        """Initialize email service with Jinja2 template environment"""
        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent.parent / "email_templates"
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    @staticmethod
    async def send_email(
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email with optional attachments

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            attachments: List of file paths to attach (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("mixed")
            message["From"] = settings.smtp_from
            message["To"] = to
            message["Subject"] = subject

            # Create alternative part for text/html
            msg_alternative = MIMEMultipart("alternative")
            message.attach(msg_alternative)

            # Add plain text version if provided
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg_alternative.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            msg_alternative.attach(part2)

            # Add attachments
            if attachments:
                for filepath in attachments:
                    if not os.path.exists(filepath):
                        logger.warning(f"Attachment not found: {filepath}")
                        continue

                    try:
                        with open(filepath, 'rb') as f:
                            part = MIMEApplication(f.read())
                            filename = os.path.basename(filepath)
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=filename
                            )
                            message.attach(part)
                        logger.info(f"Attached file: {filename}")
                    except Exception as e:
                        logger.error(f"Failed to attach file {filepath}: {e}")

            # Send email
            if settings.smtp_host == "console":
                # Development mode - print to console
                print("\n" + "=" * 80)
                print(f"EMAIL TO: {to}")
                print(f"SUBJECT: {subject}")
                print("=" * 80)
                print(html_content if html_content else text_content)
                print("=" * 80 + "\n")

                logger.info("=" * 80)
                logger.info(f"EMAIL TO: {to}")
                logger.info(f"SUBJECT: {subject}")
                logger.info("=" * 80)
                logger.info(html_content if html_content else text_content)
                logger.info("=" * 80)
                return True

            # Send via SMTP
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
                start_tls=settings.smtp_use_ssl,
            )

            logger.info(f"Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    @staticmethod
    async def send_verification_email(email: str, token: str, username: str) -> bool:
        """
        Send email verification link

        Args:
            email: User email address
            token: Verification token
            username: Username for personalization

        Returns:
            True if email was sent successfully
        """
        verification_url = f"{settings.app_url}/verify-email/{token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #0d6efd;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #0d6efd;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    color: #6c757d;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verificação de Email</h1>
                </div>
                <div class="content">
                    <p>Olá <strong>{username}</strong>,</p>

                    <p>Obrigado por se registrar no PDF Form Filler!</p>

                    <p>Para completar seu cadastro e ativar sua conta, por favor clique no botão abaixo para verificar seu endereço de email:</p>

                    <div style="text-align: center;">
                        <a href="{verification_url}" class="button">Verificar Email</a>
                    </div>

                    <p>Ou copie e cole este link no seu navegador:</p>
                    <p style="word-break: break-all; background-color: #e9ecef; padding: 10px; border-radius: 3px;">
                        {verification_url}
                    </p>

                    <p><strong>Este link expira em {settings.email_verification_expire_hours} horas.</strong></p>

                    <p>Se você não criou uma conta, por favor ignore este email.</p>
                </div>
                <div class="footer">
                    <p>PDF Form Filler - Sistema de Gerenciamento de Formulários</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Verificação de Email - PDF Form Filler

        Olá {username},

        Obrigado por se registrar no PDF Form Filler!

        Para completar seu cadastro, por favor acesse o link abaixo para verificar seu email:

        {verification_url}

        Este link expira em {settings.email_verification_expire_hours} horas.

        Se você não criou uma conta, por favor ignore este email.

        ---
        PDF Form Filler - Sistema de Gerenciamento de Formulários
        """

        return await EmailService.send_email(
            to=email,
            subject="Verifique seu email - PDF Form Filler",
            html_content=html_content,
            text_content=text_content
        )

    async def send_pdf_notification(
        self,
        to_email: str,
        to_name: str,
        template_name: str,
        pdf_path: str,
        request_name: Optional[str] = None,
        notes: Optional[str] = None,
        requester_name: Optional[str] = None,
    ) -> bool:
        """
        Send notification with PDF attachment

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            template_name: Name of the PDF template
            pdf_path: Path to filled PDF file
            request_name: Optional request name
            notes: Optional notes
            requester_name: Name of who filled the form

        Returns:
            True if sent successfully
        """
        subject = f"PDF Preenchido: {request_name or template_name}"

        context = {
            'recipient_name': to_name,
            'template_name': template_name,
            'request_name': request_name,
            'notes': notes,
            'pdf_filename': os.path.basename(pdf_path),
            'requester_name': requester_name,
        }

        try:
            # Render HTML template
            html_template = self.jinja_env.get_template("pdf_ready.html")
            html_content = html_template.render(**context)

            # Render text template
            try:
                text_template = self.jinja_env.get_template("pdf_ready.txt")
                text_content = text_template.render(**context)
            except Exception:
                # Fallback to simple text
                text_content = f"""
Olá {to_name},

Seu PDF foi preenchido e está pronto!

Template: {template_name}
{"Preenchido por: " + requester_name if requester_name else ""}
{"Nome da requisição: " + request_name if request_name else ""}
{"Observações: " + notes if notes else ""}

O PDF está anexado a este email.

---
PDF Form Filler
                """

            return await self.send_email(
                to=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                attachments=[pdf_path]
            )

        except Exception as e:
            logger.error(f"Failed to send PDF notification: {e}")
            return False

    async def send_request_completed_notification(
        self,
        to_email: str,
        to_name: str,
        request_name: str,
        template_name: str,
        completed_count: int,
        pdf_paths: Optional[List[str]] = None,
    ) -> bool:
        """
        Send notification when a request is completed

        Args:
            to_email: Recipient email address
            to_name: Recipient name
            request_name: Name of the request
            template_name: Name of the template used
            completed_count: Number of PDFs generated
            pdf_paths: Optional list of PDF paths to attach

        Returns:
            True if sent successfully
        """
        subject = f"Requisição Completada: {request_name}"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #28a745;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }}
        .content {{
            background-color: #f8f9fa;
            padding: 30px;
            border-radius: 0 0 5px 5px;
        }}
        .info {{
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 20px;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Requisição Completada</h1>
        </div>
        <div class="content">
            <p>Olá <strong>{to_name}</strong>,</p>

            <p>Sua requisição foi processada com sucesso!</p>

            <div class="info">
                <p><strong>Requisição:</strong> {request_name}</p>
                <p><strong>Template:</strong> {template_name}</p>
                <p><strong>PDFs Gerados:</strong> {completed_count}</p>
            </div>

            <p>{"Os PDFs estão anexados a este email." if pdf_paths else "Você pode acessar os PDFs na plataforma."}</p>

            <p>Obrigado por usar o PDF Form Filler!</p>
        </div>
        <div class="footer">
            <p>PDF Form Filler - Sistema de Gerenciamento de Formulários</p>
        </div>
    </div>
</body>
</html>
        """

        text_content = f"""
Requisição Completada - PDF Form Filler

Olá {to_name},

Sua requisição foi processada com sucesso!

Requisição: {request_name}
Template: {template_name}
PDFs Gerados: {completed_count}

{"Os PDFs estão anexados a este email." if pdf_paths else "Você pode acessar os PDFs na plataforma."}

Obrigado por usar o PDF Form Filler!

---
PDF Form Filler - Sistema de Gerenciamento de Formulários
        """

        return await self.send_email(
            to=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=pdf_paths
        )
