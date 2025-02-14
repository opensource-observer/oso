import logging

import duckdb
from oso_dagster.assets.defillama import DEFILLAMA_PROTOCOLS, defillama_slug_to_name

from .config import RowRestriction, TableMappingConfig, TableMappingDestination

logger = logging.getLogger(__name__)

DUCKDB_SOURCES_SCHEMA_PREFIX = "sources"

TABLE_MAPPING: TableMappingConfig = {
    "opensource-observer.op_atlas.project": "bigquery.op_atlas.project",
    "opensource-observer.op_atlas.project_contract": "bigquery.op_atlas.project_contract",
    "opensource-observer.op_atlas.project_links": "bigquery.op_atlas.project_links",
    "opensource-observer.op_atlas.project_repository": "bigquery.op_atlas.project_repository",
    "opensource-observer.oso_playground.int_deployers": "bigquery.oso.int_deployers",
    "opensource-observer.oso_playground.int_deployers_by_project": "bigquery.oso.int_deployers_by_project",
    "opensource-observer.oso_playground.int_events__blockchain": "bigquery.oso.int_events__blockchain",
    "opensource-observer.oso_playground.int_first_time_addresses": "bigquery.oso.int_first_time_addresses",
    "opensource-observer.oso_playground.int_factories": "bigquery.oso.int_factories",
    "opensource-observer.oso_playground.int_proxies": "bigquery.oso.int_proxies",
    "opensource-observer.oso_playground.int_superchain_potential_bots": "bigquery.oso.int_superchain_potential_bots",
    "opensource-observer.oso_playground.stg_deps_dev__dependencies": "bigquery.oso.stg_deps_dev__dependencies",
    "opensource-observer.oso_playground.stg_deps_dev__packages": "bigquery.oso.stg_deps_dev__packages",
    "opensource-observer.oso_playground.stg_farcaster__addresses": "bigquery.oso.stg_farcaster__addresses",
    "opensource-observer.oso_playground.stg_farcaster__profiles": "bigquery.oso.stg_farcaster__profiles",
    "opensource-observer.oso_playground.stg_github__events": "bigquery.oso.stg_github__events",
    "opensource-observer.oso_playground.stg_lens__owners": "bigquery.oso.stg_lens__owners",
    "opensource-observer.oso_playground.stg_lens__profiles": "bigquery.oso.stg_lens__profiles",
    "opensource-observer.oso_playground.stg_open_collective__deposits": TableMappingDestination(
        row_restriction=RowRestriction(time_column="created_at"),
        table="bigquery.oso.stg_open_collective__deposits",
    ),
    "opensource-observer.oso_playground.stg_open_collective__expenses": TableMappingDestination(
        row_restriction=RowRestriction(time_column="created_at"),
        table="bigquery.oso.stg_open_collective__expenses",
    ),
    "opensource-observer.ossd.collections": "bigquery.ossd.collections",
    "opensource-observer.ossd.projects": "bigquery.ossd.projects",
    "opensource-observer.ossd.repositories": "bigquery.ossd.repositories",
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


def reset_local_duckdb(path: str):
    conn = duckdb.connect(path)
    response = conn.query("SHOW ALL TABLES")
    schema_names = response.df()["schema"].unique().tolist()
    for schema_name in schema_names:
        if not schema_name.startswith(DUCKDB_SOURCES_SCHEMA_PREFIX):
            logger.info(f"dropping schema {schema_name}")
            conn.query(f"DROP schema {schema_name} cascade")
