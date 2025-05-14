import asyncio
import os
from email.message import EmailMessage
from aiosmtplib import SMTP
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env


load_dotenv()  # Загружает переменные из .env


async def send_email(to_email: str, subject: str, body_text: str, body_html: str = None):
    message = EmailMessage()
    message["From"] = os.getenv("SMTP_USER")
    message["To"] = to_email
    message["Subject"] = subject

    # Текстовая часть
    message.set_content(body_text)

    # HTML-часть (если передана)
    if body_html:
        message.add_alternative(body_html, subtype="html")

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")

    try:
        smtp = SMTP(hostname=smtp_host, port=smtp_port, use_tls=False)
        await smtp.connect()
        # await smtp.starttls()
        await smtp.login(smtp_user, smtp_pass)
        await smtp.send_message(message)
        await smtp.quit()
    except Exception as e:
        print("Ошибка отправки:", e)
        return False
    else:
        return True
html_body = """
<html>
  <body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #2c3e50;">Привет!</h2>
    <p>Вы только что вошли в систему. Если это были не вы — <a href="#">немедленно измените пароль</a>.</p>
    <p style="color: #888;">Это автоматическое письмо. Пожалуйста, не отвечайте на него.</p>
    <hr>
    <p style="font-size: 12px;">FinCubes © 2025</p>
  </body>
</html>
"""

if __name__ == '__main__':
    asyncio.run(send_email(
        to_email="9999269010dddd@gmail.com",
        subject="Вход в систему",
        body_text="Вы вошли в систему. Если это были не вы — смените пароль.",
        body_html=html_body
    ))
