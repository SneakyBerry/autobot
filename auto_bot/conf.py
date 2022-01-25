import logging
from typing import Union

from pydantic import BaseSettings
from yarl import URL


class AppConfig(BaseSettings):

    LOGLEVEL: Union[int, str] = logging.DEBUG

    API_TOKEN: str

    WEBHOOK_HOST: str
    WEBHOOK_PATH: str = "/telegram/webhook"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    DATABASE_URL: str

    @property
    def WEBHOOK_URL(self):
        return URL(self.WEBHOOK_HOST).join(URL(self.WEBHOOK_PATH))


settings = AppConfig()
logging.basicConfig(level=settings.LOGLEVEL)
logging.info(settings)
