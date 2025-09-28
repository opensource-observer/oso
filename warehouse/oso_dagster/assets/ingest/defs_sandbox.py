from dagster import Definitions, load_assets_from_modules, resource

import warehouse.oso_dagster.assets.ingest.db.postgres.orders_replication_asset as pg_mod
import warehouse.oso_dagster.assets.ingest.graphql.countries.countries_asset as countries_mod

# ----- assets (keep only the three) -----
import warehouse.oso_dagster.assets.ingest.rest.jsonplaceholder.posts_asset as jsonplaceholder_posts_mod

# ----- secrets: import official types if available, but DON'T redefine them -----
# We define a neutral base class for our local dev resolver to satisfy type checkers.
try:
    # Import so assets can use the canonical SecretReference at runtime elsewhere.
    pass  # noqa: F401
except Exception:
    # If the upstream module isn't importable locally, we still provide a working resolver;
    # we deliberately avoid redefining the same class names to keep pyright happy.
    pass

import os


class BaseSecretResolver:
    """Minimal interface used by local/dev runs."""

    def resolve(self, ref) -> bytes:  # no type to avoid cross-module type conflicts
        raise NotImplementedError

    def resolve_as_str(self, ref) -> str:
        return self.resolve(ref).decode("utf-8")


class DevEnvSecretResolver(BaseSecretResolver):
    """Reads secrets from env: DAGSTER__<GROUP>__<KEY>."""

    def resolve(self, ref) -> bytes:
        group = getattr(ref, "group_name", None)
        key = getattr(ref, "key", None)
        if not group or not key:
            raise RuntimeError("Secret reference must expose .group_name and .key")
        env = f"DAGSTER__{str(group).upper()}__{str(key).upper()}"
        val = os.getenv(env)
        if val is None:
            raise RuntimeError(f"Missing env: {env}")
        return val.encode("utf-8")


@resource
def secret_resolver():
    # In CI/dev this resolver looks at environment variables.
    return DevEnvSecretResolver()


assets = load_assets_from_modules([jsonplaceholder_posts_mod, countries_mod, pg_mod])
defs = Definitions(assets=assets, resources={"secret_resolver": secret_resolver})
