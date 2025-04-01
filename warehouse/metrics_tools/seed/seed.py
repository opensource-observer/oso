import os

from metrics_tools.seed.loader import TrinoLoader


async def db_seed():
    loader = TrinoLoader()
    try:
        path, _ = os.path.split(os.path.realpath(__file__))
        schema_files: dict[str, list[str]] = {}
        for root, _, files in os.walk(os.path.join(path, "schemas")):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    schema_files.setdefault(os.path.split(root)[1], []).append(file)

        for schema, files in schema_files.items():
            await loader.create_schema(schema)
            for file in files:
                module = __import__(
                    f"{__name__.rsplit('.', 1)[0]}.schemas.{schema}.{file[:-3]}",
                    fromlist=["seed"],
                )
                if hasattr(module, "seed"):
                    await module.seed(loader)
    finally:
        await loader.close()
