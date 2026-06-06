import os
import smtplib
from email.mime.text import MIMEText


def send_email(subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")

    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("EMAIL_TO")

    with smtplib.SMTP_SSL(
        os.getenv("EMAIL_HOST"),
        int(os.getenv("EMAIL_PORT", "465"))
    ) as server:
        server.login(
            os.getenv("EMAIL_USER"),
            os.getenv("EMAIL_PASSWORD")
        )
        server.send_message(msg)