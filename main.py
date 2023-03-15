from fastapi import Depends, FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import logging
from settings import get_settings, DevSettings, ProdSettings

app = FastAPI()


async def send_email(settings=Depends(get_settings)):
    message = MessageSchema(
        subject="Test Email",
        recipients=[settings.RECIPIENTS],
        body="Hello, this is a test email!",
        subtype="plain",
    )
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_TLS=False,
        MAIL_SSL=False,
        USE_CREDENTIALS=False,
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
async def info(settings: DevSettings | ProdSettings = Depends(get_settings)):
    return send_email()


@app.get("/")
async def root():
    return {"Hello"}
