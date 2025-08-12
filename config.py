from dotenv import load_dotenv
load_dotenv()
from pydantic_settings import BaseSettings  # type: ignore

class Settings(BaseSettings):
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    SECRET_KEY: str
    APP_PORT: int | None = None
    EMAIL_USER: str | None = None
    EMAIL_PASS: str | None = None
    DATABASE_URL: str | None = None

    @property
    def constructed_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

settings = Settings()


