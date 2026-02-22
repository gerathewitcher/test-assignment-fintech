from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_PORT: int = 8000
    API_KEY: str = "dev-static-api-key"
    POSTGRES_USER: str = "directory"
    POSTGRES_PASSWORD: str = "directory"
    POSTGRES_DB: str = "directory"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_POOL_SIZE: int = 10
    DATABASE_POOL_TTL: int = 300
    DATABASE_POOL_PRE_PING: int = 10

    @computed_field
    @property
    def POSTGRES_DSN(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=f"{self.POSTGRES_DB}",
        )


settings = Settings()
