"""
Email service for sending emails
"""
import logging
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from ..config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    async def send_email(
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to: Recipient email address
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)

        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = settings.smtp_from
            message["To"] = to
            message["Subject"] = subject

            # Add plain text version if provided
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)

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
