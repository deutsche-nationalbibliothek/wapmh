from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    repository_name: str = "Webarchive OAI-PMH Endpoint"
    description: str = "This is the OAI-PMH endpoint of the Webarchive."
    admin_emails: Optional[list[str]] = None

    sparql_endpoint: str = "http://localhost:5000/query"

    model_config = SettingsConfigDict(env_file="default.env")