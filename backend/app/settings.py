from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settins(BaseSettings):
    app_name: str = "My Card Game"
    debug: bool = True
    database_url: str = "sqlite:///./shop.db"
    cors_origins: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    static_dir: str = "static"
    images_dir: str = "static/images"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="UTF-8",
        env_prefix="APP",
    )


settings = Settins()
