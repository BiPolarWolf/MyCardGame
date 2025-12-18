from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    # это настройка самого нашего settings
    # чтобы он знал откуда брать переменные окружения
    # env_prefix - смотрит на переменные которые начинаются с "APP"
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="UTF-8",
        env_prefix="APP",
    )


# кароче это самый настоящий settings.py но в виде класса который
# подтягивает все его настройки из .env который лежит в корне нашего бекенда
# тут можно указать какие то значение по умолчанию , установить типы чтобы знать
# и все эти settings будут хранится в standalone экземпляре класса Settings
settings = Settings()
