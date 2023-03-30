import os
import datetime as dt

from fastapi import Depends, FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from settings import get_settings, DevSettings, ProdSettings
from precipitation import PrecipitationData

# Import the logging configuration module
from logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI()


def prepare_prepcipitation_rpt(settings: (DevSettings | ProdSettings | None)):
    base_url = settings.PSL_PRECIP_DATASETS_URL
    ncfile_url = f"{base_url}precip.{dt.datetime.today().year}.nc"
    output_file = os.path.join("data", "precip.csv")
    sub_dir = "data/nc"
    file_name = "precip.2022.nc"
    file_path = os.path.abspath(os.path.join(sub_dir, file_name))

    precip_data = PrecipitationData(file_path, settings)
    precip_data.read_data()

    # mean, median, std_dev = precip_data.compute_statistics()
    # print(f"Mean: {mean}, Median: {median}, Standard Deviation: {std_dev}")

    # subset = precip_data.extract_subset("2023-03-15", "2023-03-20")
    # print(subset)

    precip_data.save_to_csv(output_file)


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
        logger.error(f"Failed to send email: {str(e)}")
    else:
        logger.info(f"Email sent successfully: {response}")


@app.get("/info")
async def info(settings: (DevSettings | ProdSettings | None) = Depends(get_settings)):
    logger.info(f"Setting: {settings}")
    await prepare_prepcipitation_rpt(settings=settings)
    return {"message": "Email sent!"}


@app.get("/")
async def root():
    return {"msg": "Hello World"}
