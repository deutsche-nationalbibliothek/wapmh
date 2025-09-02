from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    repository_name: str = "Webarchive OAI-PMH Endpoint"
    description: str = "This is the OAI-PMH endpoint of the Webarchive."
    admin_emails: Optional[list[str]] = None

    sparql_endpoint: str = ""
    graph_path: str = ""
    query_path: str = ""

    limit: int = ""

    model_config = SettingsConfigDict(env_file=["default.env", "custom.env"])
