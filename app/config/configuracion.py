from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion centralizada del proyecto, leida desde el archivo .env"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8-sig")

    anthropic_api_key: str = ""
    claude_mock_mode: bool = True
    database_url: str = ""
    limite_historial_mensajes: int = 30

    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""


settings = Settings()