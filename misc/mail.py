from email.message import EmailMessage
from typing import Optional

from aiosmtplib import SMTP

from config import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER
from misc.errors import APIError, ErrorCode
from misc.templates import get_template


async def send_email(
    to_email: str, subject: str, body_text: str, body_html: Optional[str] = None
):
    message = EmailMessage()
    message["From"] = SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body_text)

    if body_html:
        message.add_alternative(body_html, subtype="html")

    try:
        smtp = SMTP(hostname=SMTP_HOST, port=SMTP_PORT, use_tls=False)
        await smtp.connect()
        await smtp.login(SMTP_USER, SMTP_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
    except Exception as exc:
        raise APIError(ErrorCode.SEND_EMAIL_EXCEPTION) from exc


async def send_confirm_code(email: str, code: str):
    html = get_template("mail_confirm_code.html", code=code)
    text = f"""Код подтверждения для аккаунта FinCubes:\n\n{code}\n\nЕсли вы не запрашивали это действие, просто проигнорируйте письмо."""
    await send_email(
        to_email=email,
        subject="📧 Подтверждение аккаунта — FinCubes",
        body_text=text,
        body_html=html,
    )


async def send_reset_password(email: str, user_id: int, token: str):
    html = get_template("mail_reset_password.html",
                        user_id=user_id, token=token)
    text = f"""Вы запросили сброс пароля на FinCubes.\n\nЧтобы сбросить пароль, перейдите по ссылке:\nhttps://fincubes.ru/reset-password?token={token}&user_id={user_id}\n\nЕсли вы не запрашивали сброс, проигнорируйте это сообщение."""
    await send_email(
        to_email=email,
        subject="🔐 Сброс пароля — FinCubes",
        body_text=text,
        body_html=html,
    )
