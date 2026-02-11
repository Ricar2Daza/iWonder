from datetime import datetime
import logging

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

from core.config import settings

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS
)


async def send_reset_email(email: str, token: str):
    reset_link = f"http://localhost:3000/reset-password?token={token}"
    html = f"""
    <p>Has solicitado restablecer tu contraseña en iWonder.</p>
    <p>Haz clic en el siguiente enlace para continuar:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Si no solicitaste este cambio, puedes ignorar este correo.</p>
    <p>Este enlace expirará en 1 hora.</p>
    """

    message = MessageSchema(
        subject="Restablecimiento de Contraseña - iWonder",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        print(f"FAILED TO SEND EMAIL. Link: {reset_link}")
