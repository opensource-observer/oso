import logging
import os
import typing as t

import duckdb
import psycopg2
from google.cloud import bigquery
from metrics_tools.local.loader import (
    DuckDbDestinationLoader,
    PostgresDestinationLoader,
)
from oso_dagster.assets.defillama import DEFILLAMA_PROTOCOLS, defillama_slug_to_name

from .config import Config, DestinationLoader, RowRestriction, TableMappingDestination

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "opensource-observer")

DUCKDB_SOURCES_SCHEMA_PREFIX = "sources"

TABLE_MAPPING: t.Dict[str, str | TableMappingDestination] = {
    "opensource-observer.oso_playground.int_deployers": "bigquery.oso.int_deployers",
    "opensource-observer.oso_playground.int_deployers_by_project": "bigquery.oso.int_deployers_by_project",
    "opensource-observer.oso_playground.int_events__blockchain": "bigquery.oso.int_events__blockchain",
    "opensource-observer.oso_playground.int_events__github": "bigquery.oso.int_events__github",
    "opensource-observer.oso_playground.int_events__dependencies": "bigquery.oso.int_events__dependencies",
    "opensource-observer.oso_playground.int_events__open_collective": "bigquery.oso.int_events__open_collective",
    "opensource-observer.oso_playground.int_first_time_addresses": "bigquery.oso.int_first_time_addresses",
    "opensource-observer.oso_playground.int_factories": "bigquery.oso.int_factories",
    "opensource-observer.oso_playground.int_proxies": "bigquery.oso.int_proxies",
    "opensource-observer.oso_playground.int_superchain_potential_bots": "bigquery.oso.int_superchain_potential_bots",
    "opensource-observer.oso_playground.stg_deps_dev__packages": "bigquery.oso.stg_deps_dev__packages",
    "opensource-observer.oso_playground.stg_farcaster__addresses": "bigquery.oso.stg_farcaster__addresses",
    "opensource-observer.oso_playground.stg_farcaster__profiles": "bigquery.oso.stg_farcaster__profiles",
    "opensource-observer.oso_playground.stg_lens__owners": "bigquery.oso.stg_lens__owners",
    "opensource-observer.oso_playground.stg_lens__profiles": "bigquery.oso.stg_lens__profiles",
    "opensource-observer.oso_playground.stg_ossd__current_collections": "bigquery.oso.stg_ossd__current_collections",
    "opensource-observer.oso_playground.stg_ossd__current_projects": "bigquery.oso.stg_ossd__current_projects",
    "opensource-observer.oso_playground.stg_ossd__current_repositories": "bigquery.oso.stg_ossd__current_repositories",
    "opensource-observer.oso_playground.timeseries_events_aux_issues_by_artifact_v0": "bigquery.oso.timeseries_events_aux_issues_by_artifact_v0",
    "opensource-observer.ossd.sbom": "bigquery.ossd.sbom",
    # Only grab some data from frax for local testing
    "opensource-observer.optimism_superchain_raw_onchain_data.blocks": TableMappingDestination(
        # row_restriction=f"dt >= '{start_date.strftime("%Y-%m-%d")}' AND dt < '{end_date.strftime("%Y-%m-%d")}' AND chain_id = 252",
        row_restriction=RowRestriction(
            time_column="dt",
            wheres=["chain_id = 252"],
        ),
        table="bigquery.optimism_superchain_raw_onchain_data.blocks",
    ),
    "opensource-observer.optimism_superchain_raw_onchain_data.transactions": TableMappingDestination(
        row_restriction=RowRestriction(
            time_column="dt",
            wheres=["chain_id = 252"],
        ),
        table="bigquery.optimism_superchain_raw_onchain_data.transactions",
    ),
    "opensource-observer.optimism_superchain_raw_onchain_data.traces": TableMappingDestination(
        row_restriction=RowRestriction(
            time_column="dt",
            wheres=["chain_id = 252"],
        ),
        table="bigquery.optimism_superchain_raw_onchain_data.traces",
    ),
}

defillama_tables = {
    f"opensource-observer.defillama_tvl.{defillama_slug_to_name(slug)}": f"bigquery.defillama_tvl.{defillama_slug_to_name(slug)}"
    for slug in DEFILLAMA_PROTOCOLS
}
TABLE_MAPPING.update(defillama_tables)


def initialize_local(
    destination_loader: DestinationLoader,
    max_results_per_query: int = 0,
    max_days: int = 7,
):
    # Use the oso_dagster assets as the source of truth for configured defi
    # llama protocols for now

    Config(
        table_mapping=TABLE_MAPPING,
        max_days=max_days,
        max_results_per_query=max_results_per_query,
        project_id=PROJECT_ID,
    ).load_tables_into(destination_loader)


def initialize_local_duckdb(
    path: str, max_results_per_query: int = 0, max_days: int = 7
):
    conn = duckdb.connect(path)

    loader = DuckDbDestinationLoader(bigquery.Client(), conn)
    initialize_local(loader, max_results_per_query, max_days)


def initialize_local_postgres(
    path: str, max_results_per_query: int = 0, max_days: int = 7
):
    conn = duckdb.connect(path)

    loader = PostgresDestinationLoader(
        bigquery.Client(),
        conn,
        psycopg2.connect(
            database="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port=5432,
        ),
        postgres_host="localhost",
        postgres_db="postgres",
        postgres_user="postgres",
        postgres_password="password",
        postgres_port=5432,
    )
    initialize_local(loader, max_results_per_query, max_days)


def reset_local_duckdb(path: str):
    conn = duckdb.connect(path)
    response = conn.query("SHOW ALL TABLES")
    schema_names = response.df()["schema"].unique().tolist()
    for schema_name in schema_names:
        if not schema_name.startswith(DUCKDB_SOURCES_SCHEMA_PREFIX):
            logger.info(f"dropping schema {schema_name}")
            conn.query(f"DROP schema {schema_name} cascade")
