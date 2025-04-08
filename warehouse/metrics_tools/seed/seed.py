import importlib
import os
from typing import Literal

from metrics_tools.seed.loader import DuckDbLoader, TrinoLoader
from metrics_tools.seed.types import SeedConfig


async def db_seed(loader_type: Literal["trino", "duckdb"] = "trino"):
    loader = TrinoLoader.connect() if loader_type == "trino" else DuckDbLoader.connect()
    try:
        path, _ = os.path.split(os.path.realpath(__file__))
        for root, _, files in os.walk(os.path.join(path, "schemas")):
            schema = os.path.split(root)[1]
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    module = importlib.import_module(
                        f"metrics_tools.seed.schemas.{schema}.{file.replace(".py", "")}",
                    )
                    for item in dir(module):
                        obj = getattr(module, item)
                        if isinstance(obj, SeedConfig):
                            await loader.load(obj)

    finally:
        await loader.close()
