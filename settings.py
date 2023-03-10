from pydantic import BaseSettings, EmailStr, SecretStr, ValidationError
from typing import List
import os


class GlobalSettings(BaseSettings):
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIN_FROM_NAME: str
    RECIPIENTS: List[EmailStr] = []
    SCHEDULER_TIMEZONE: str
    SCHEDULER_TYPE: str
    SCHEDULER_HOUR: int
    SCHEDULER_MINUTE: int
    MISFIRE_GRACE_TIME: int
    EXTRACTED_DAYS: int
    TARGET_COORD_FILENAME: str
    PSL_PRECIP_DATASETS_URL: str

    TESTING: bool = False

    class Config:
        case_sensitive = False


class DevSettings(GlobalSettings):
    class Config:
        env_file = "./env/.env.testing"


class ProdSettings(GlobalSettings):
    class Config:
        env_file = "./env/.env"


def get_settings():
    try:
        env = os.getenv("ENVIRONMENT", "development")
        if env == "production":
            return ProdSettings()
        return DevSettings()
    except ValidationError as e:
        print(e)
