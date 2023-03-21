from fastapi import Depends, FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import logging
from typing import Annotated
from settings import get_settings, DevSettings, ProdSettings

app = FastAPI()


async def send_email(settings: (DevSettings | ProdSettings | None)):
    message = MessageSchema(
        subject="Test Email",
        recipients=settings.RECIPIENTS,
        body="Hello, this is a test email!",
        subtype="plain",
    )
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD.get_secret_value(),
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        TEMPLATE_FOLDER="./templates/",
    )
    fm = FastMail(conf)
    try:
        response = await fm.send_message(message)
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
    else:
        logging.info(f"Email sent successfully: {response}")


@app.get("/info")
async def info(settings: (DevSettings | ProdSettings | None) = Depends(get_settings)):
    logging.info(f"Setting: {settings}")
    await send_email(settings=settings)
    return {"message": "Email sent!"}


@app.get("/")
async def root():
    return {"Hello"}
