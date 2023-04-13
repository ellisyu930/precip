import asyncio
import os
import datetime as dt

from fastapi import Depends, FastAPI
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from settings import get_settings, DevSettings, ProdSettings
from precipitation import PrecipitationData
from apscheduler.schedulers.background import BackgroundScheduler

# Import the logging configuration module
from logging_config import get_logger

logger = get_logger(__name__)

app = FastAPI()

# Define the scheduler
scheduler = BackgroundScheduler()


# Add the scheduler's start and stop methods to the startup and shutdown events of FastAPI
@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    scheduler.configure(timezone=settings.SCHEDULER_TIMEZONE)
    if settings.SCHEDULER_TYPE == "cron":
        scheduler.add_job(
            prepare_prepcipitation_rpt,
            settings.SCHEDULER_TYPE,
            hour=settings.SCHEDULER_HOUR,
            minute=settings.SCHEDULER_MINUTE,
            misfire_grace_time=settings.MISFIRE_GRACE_TIME,
            args=[settings],
        )
    else:
        scheduler.add_job(
            prepare_prepcipitation_rpt,
            settings.SCHEDULER_TYPE,
            hours=settings.SCHEDULER_INT_HOURS,
            minutes=settings.SCHEDULER_INT_MINUTES,
            misfire_grace_time=settings.MISFIRE_GRACE_TIME,
            args=[settings],
        )

    scheduler.start()
    print("Scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler stopped")


def prepare_prepcipitation_rpt(settings: (DevSettings | ProdSettings | None)):
    base_url = settings.PSL_PRECIP_DATASETS_URL
    ncfile_url = f"{base_url}precip.{dt.datetime.today().year}.nc"
    output_file = os.path.join("data", "precip.csv")
    sub_dir = "data/nc"
    file_name = "precip.2022.nc"
    file_path = os.path.abspath(os.path.join(sub_dir, file_name))

    precip_data = PrecipitationData(ncfile_url, settings)

    curr_time_value = precip_data.get_curr_time_value()
    prev_time_value = precip_data.get_previous_time_value()

    if curr_time_value > prev_time_value:
        precip_data.read_data()

        # mean, median, std_dev = precip_data.compute_statistics()
        # print(f"Mean: {mean}, Median: {median}, Standard Deviation: {std_dev}")

        # subset = precip_data.extract_subset("2023-03-15", "2023-03-20")
        # print(subset)

        precip_data.save_to_csv(output_file)

        file_exists = os.path.exists(output_file)

        if file_exists:
            logger.info(f"Path:{output_file}")

            asyncio.run(
                send_email(
                    settings,
                    "Precipitaion Report",
                    settings.RECIPIENTS,
                    output_file,
                )
            )
        precip_data.update_previous_time_value(curr_time_value)


async def send_email(
    settings: (DevSettings | ProdSettings | None), subject, email_to, file
):
    message = MessageSchema(
        subject=subject,
        recipients=email_to,
        body="",
        attachments=[{"file": file}],
        subtype=MessageType.html,
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
    prepare_prepcipitation_rpt(settings=settings)
    return {"message": "Email sent!"}


@app.get("/")
async def root():
    return {"msg": "Hello World"}
