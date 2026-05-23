from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    SAM_API_KEY: str
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    SERVER_NAME: str = "samgov-mcp"
    SERVER_VERSION: str = "1.0.0"
    BILLING_ENABLED: bool = True
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_SOLO: str = ""
    STRIPE_PRICE_TEAM: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""
    RATE_LIMIT_SOLO: int = 500
    RATE_LIMIT_TEAM: int = 2000
    RATE_LIMIT_ENTERPRISE: int = 10000
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    DEV_MODE: bool = False
    DEV_API_KEY: str = "dev-key-local"

settings = Settings()
