import asyncio
from email.message import EmailMessage

import aiosmtplib

from config import config, logger


async def send_email(
    recipient: str,
    subject: str,
    body: str,
    sender=config.EMAIL,
    password=config.EMAIL_PASSWORD,
    host=config.EMAIL_HOST,
    port: int = 465,
    use_tls: bool = True,  # Sin TLS, toda la comunicación con el servidor SMTP (incluyendo usuario, contraseña y el contenido de los correos) se envía en texto plano
):
    """
    Envía un correo electrónico de forma asíncrona.

    Args:
        recipient: Dirección del destinatario
        subject: Asunto del correo
        body: Cuerpo del mensaje (puede ser HTML o texto plano)
        sender: Remitente (por defecto julia.m@jumo.cat)
        password: Contraseña del remitente
        host: Servidor SMTP (por defecto smtp.jumo.cat)
        port: Puerto SMTP (por defecto 587)
        use_tls: Usar TLS (por defecto True)
    """
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(
        body
    )  # set_content para texto plano o add_alternative para HTML

    try:
        await aiosmtplib.send(
            message,
            hostname=host,
            port=port,
            username=sender,
            password=password,
            use_tls=use_tls,
        )
        logger.info(f"Correo enviado exitosamente a {recipient}")
        return True

    except Exception as e:
        logger.error(f"Error al enviar el correo: {str(e)}")
        return False


async def send_confirmation_email(user_email, url):
    body = f"Please click the link below to confirm your email \
        \n\n{url} \
        \nDon't share it with anyone"

    await send_email(
        user_email,
        "Confirmation Email",
        body,
    )


if __name__ == "__main__":

    async def main():
        await send_email(
            recipient="oslianyabel@gmail.com",
            subject="Test",
            body="Este es un mensaje de prueba enviado de forma asíncrona.",
        )

    asyncio.run(main())
