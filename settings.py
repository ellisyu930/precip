import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    API_BASE: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    TESTING: bool = False

    class Config:
        env_file = "./env/.env"


class Production(Settings):
    API_BASE = "https://example.com/api"
    DB_NAME = "production"


class Testing(Settings):
    API_BASE = "https://testing.example.com/api"
    DB_NAME = "testing"

    class Config:
        env_file = "./env/.testing.env"


def get_settings():
    env = os.getenv("ENV", "TESTING")
    if env == "PRODUCTION":
        return Production()
    return Testing()


settings = get_settings()

print("DB Host =", settings.DB_HOST)
print("DB Port =", settings.DB_PORT)

print("Override =", Production(TESTING=True).dict())
