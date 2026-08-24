from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Значения берутся из переменных окружения / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "TAPRIME"

    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/taprime"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа

    # Первый суперадмин платформы, создаётся при первом старте, если ещё не существует
    FIRST_SUPERADMIN_EMAIL: str = "admin@taprime.local"
    FIRST_SUPERADMIN_PASSWORD: str = "change-me-in-production"


settings = Settings()
