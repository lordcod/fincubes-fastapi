from email.message import EmailMessage
from typing import Optional

from aiosmtplib import SMTP

from app.core.config import settings
from app.core.errors import APIError, ErrorCode
from app.integrations.yandexcloud import make_cloud_url
from app.shared.utils.templates import get_template


async def send_email(
    to_email: str, subject: str, body_text: str, body_html: Optional[str] = None
):
    message = EmailMessage()
    message["From"] = settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject

    message.set_content(body_text)

    if body_html:
        message.add_alternative(body_html, subtype="html")

    try:
        smtp = SMTP(hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT, use_tls=False)
        await smtp.connect()
        await smtp.login(settings.SMTP_USER,  settings.SMTP_PASSWORD)
        await smtp.send_message(message)
        await smtp.quit()
    except Exception as exc:
        raise APIError(ErrorCode.SEND_EMAIL_EXCEPTION) from exc


async def send_confirm_code(email: str, code: str):
    html = await get_template(
        "v2/verify-email.html",
        verificationCode=code,
        verificationLink=f"https://fincubes.ru/email/confirm?code={code}"
    )
    text = f"""Код подтверждения для аккаунта FinCubes:\n\n{code}\n\nЕсли вы не запрашивали это действие, просто проигнорируйте письмо."""
    await send_email(
        to_email=email,
        subject="📧 Подтверждение аккаунта — FinCubes",
        body_text=text,
        body_html=html,
    )


async def send_reset_password(email: str, user_id: int, token: str):
    html = await get_template(
        "v2/reset-password.html",
        resetLink=f"https://fincubes.ru/password/confirm?token={token}&user_id={user_id}"
    )
    text = f"""Вы запросили сброс пароля на FinCubes.\n\nЧтобы сбросить пароль, перейдите по ссылке:\nhttps://fincubes.ru/password/confirm?token={token}&user_id={user_id}\n\nЕсли вы не запрашивали сброс, проигнорируйте это сообщение."""
    await send_email(
        to_email=email,
        subject="🔐 Сброс пароля — FinCubes",
        body_text=text,
        body_html=html,
    )


async def send_warn_unverified(email: str, hours_delay: int):
    """
    Send warning email to user that their account will be deleted
    if not verified within `hours_delay` hours.
    """
    html = await get_template(
        "v2/account-deletion.html",
        hoursRemaining=hours_delay,
        verificationLink="https://fincubes.ru/confirm",
        logoUrl=make_cloud_url("emails/logo.png"),
    )

    text = (
        f"Аккаунт будет удалён через {hours_delay} часов.\n\n"
        f"Внимание! Ваш аккаунт FinCubes ещё не подтверждён.\n\n"
        f"Чтобы подтвердить email, перейдите по ссылке:\n"
        f"https://fincubes.ru/confirm\n\n"
        f"Если вы уже подтвердили почту или хотите удалить аккаунт, просто проигнорируйте это письмо."
    )

    await send_email(
        to_email=email,
        subject="⚠️ Подтвердите почту — FinCubes",
        body_text=text,
        body_html=html,
    )
