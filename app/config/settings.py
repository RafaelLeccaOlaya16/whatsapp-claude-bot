from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion centralizada del proyecto, leida desde el archivo .env"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig")

    anthropic_api_key: str = ""
    claude_mock_mode: bool = True


settings = Settings()
