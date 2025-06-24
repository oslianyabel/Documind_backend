import logging
from functools import lru_cache
from typing import Optional
from openai import AsyncOpenAI

from pydantic_settings import BaseSettings, SettingsConfigDict

from logging_conf import configure_logging

configure_logging()
logger = logging.getLogger("app")


class BaseConfig(BaseSettings):
    ENV_STATE: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


class GlobalConfig(BaseConfig):
    DATABASE_URL: Optional[str] = None

    EMAIL: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_HOST: Optional[str] = None
    ADMIN_EMAIL: Optional[str] = None

    B2_KEY_ID: Optional[str] = None
    B2_APPLICATION_KEY: Optional[str] = None
    B2_BUCKET_NAME: Optional[str] = None

    SECRET_KEY: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    DOCUMENT_PATH: Optional[str] = None

    DOMAIN: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None


class DevConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="DEV_")


class ProdConfig(GlobalConfig):
    model_config = SettingsConfigDict(env_prefix="PROD_")


@lru_cache
def get_config(env_state: str) -> GlobalConfig:
    configs = {
        "dev": DevConfig,
        "prod": ProdConfig,
    }
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)


if __name__ == "__main__":
    print(config)
