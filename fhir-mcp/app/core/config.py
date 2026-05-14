from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    HTTP_CLIENT: str
    OPENAPI_SPEC: str
    IAM_JWKS_URL: str
    IAM_ISSUER: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
