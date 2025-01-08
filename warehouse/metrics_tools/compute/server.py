"""This is the main entrypoint for uvicorn or fastapi to load the mcs server."""

from .app import app_factory, default_lifecycle
from .types import AppConfig

app = app_factory(
    default_lifecycle,
    # App config won't resolve types correctly due to pydantic's BaseSettings
    AppConfig(),  # type: ignore
)
