from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    github_token: str = ""
    notion_api_key: str = ""
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
