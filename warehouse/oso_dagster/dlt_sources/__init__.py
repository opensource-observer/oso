from typing import (
    TypedDict,
    Dict,
    Any,
    cast,
    Unpack,
    Sequence,
    Optional,
    List,
    Iterable,
)
from functools import partial
from dagster import AssetKey
import dlt
from dlt.extract.resource import DltResource
from dlt.pipeline.pipeline import Pipeline
from dlt.sources import DltSource
from dlt.sources.credentials import ConnectionStringCredentials
from dagster import AssetExecutionContext
from dagster_embedded_elt.dlt import (
    DagsterDltTranslator,
    dlt_assets,
    DagsterDltResource,
)

from .sql_database import sql_database


class DBCredentialsReference(TypedDict):
    connection_string: str | Dict[str, Any]


def sql_source(**kwargs: Unpack[DBCredentialsReference]):
    creds = ConnectionStringCredentials(**kwargs)
    return partial(sql_database, creds)


def sql_asset(source_name: str, source_credential_reference: str):
    translator = PrefixedDltTranslator(source_name)
    source = sql_source(connection_string=source_credential_reference)()
    pipeline = dlt.pipeline(
        pipeline_name=f"{source_name}_to_bigquery",
        destination="bigquery",
        dataset_name="temp_source",
        progress="log",
    )

    @dlt_assets(
        dlt_source=source, dlt_pipeline=pipeline, dlt_dagster_translator=translator
    )
    def _asset(context: AssetExecutionContext, dlt: DagsterDltResource):
        yield from dlt.run(context=context)

    return _asset


class PrefixedDltTranslator(DagsterDltTranslator):
    def __init__(self, source_name: str, prefix: Optional[Sequence[str]] = None):
        self._prefix = prefix or cast(Sequence[str], [])
        self._source_name = source_name

    def get_asset_key(self, resource: DltResource) -> AssetKey:
        key: List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append(resource.name)
        print("BOOOOP")
        print(key)
        return AssetKey(key)

    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """We don't include the source here in the graph. It's not a necessary stub to represent"""
        key: List[str] = []
        key.extend(self._prefix)
        key.append("source")
        key.append(self._source_name)
        key.append(resource.name)
        return [AssetKey(key)]
