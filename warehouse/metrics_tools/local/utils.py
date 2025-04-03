import logging

import duckdb

from .config import RowRestriction, TableMappingConfig, TableMappingDestination

logger = logging.getLogger(__name__)

DUCKDB_SOURCES_SCHEMA_PREFIX = "sources"

TABLE_MAPPING: TableMappingConfig = {
    "opensource-observer.farcaster.profiles": "bigquery.farcaster.profiles",
    "opensource-observer.farcaster.verifications": "bigquery.farcaster.verifications",
    "opensource-observer.lens_v2_polygon.profile_metadata": "bigquery.lens_v2_polygon.profile_metadata",
    "opensource-observer.lens_v2_polygon.profile_ownership_history": "bigquery.lens_v2_polygon.profile_ownership_history",
    "opensource-observer.op_atlas.application": "bigquery.op_atlas.application",
    "opensource-observer.op_atlas.project": "bigquery.op_atlas.project",
    "opensource-observer.op_atlas.project__defi_llama_slug": "bigquery.op_atlas.project__defi_llama_slug",
    "opensource-observer.op_atlas.project__farcaster": "bigquery.op_atlas.project__farcaster",
    "opensource-observer.op_atlas.project__website": "bigquery.op_atlas.project__website",
    "opensource-observer.op_atlas.project_contract": "bigquery.op_atlas.project_contract",
    "opensource-observer.op_atlas.project_links": "bigquery.op_atlas.project_links",
    "opensource-observer.op_atlas.project_repository": "bigquery.op_atlas.project_repository",
    "opensource-observer.op_atlas.project_organization": "bigquery.op_atlas.project_organization",
    "opensource-observer.open_collective.deposits": TableMappingDestination(
        row_restriction=RowRestriction(time_column="created_at"),
        table="bigquery.open_collective.deposits",
    ),
    "opensource-observer.open_collective.expenses": TableMappingDestination(
        row_restriction=RowRestriction(time_column="created_at"),
        table="bigquery.open_collective.expenses",
    ),
    ### TODO start: remove oso_playground dependency
    "opensource-observer.oso_playground.stg_deps_dev__packages": "bigquery.oso.stg_deps_dev__packages",
    ### TODO end
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
    "opensource-observer.optimism_superchain_4337_account_abstraction_data.useroperationevent_logs_v2": TableMappingDestination(
        row_restriction=RowRestriction(
            time_column="dt",
            wheres=["chain_id = 252"],
        ),
        table="bigquery.optimism_superchain_4337_account_abstraction_data.useroperationevent_logs_v2",
    ),
    "opensource-observer.optimism_superchain_4337_account_abstraction_data.enriched_entrypoint_traces_v2": TableMappingDestination(
        row_restriction=RowRestriction(
            time_column="dt",
            wheres=["chain_id = 252"],
        ),
        table="bigquery.optimism_superchain_4337_account_abstraction_data.enriched_entrypoint_traces_v2",
    ),
    "opensource-observer.defillama.tvl_events": "bigquery.defillama.tvl_events",
    "opensource-observer.sqlmesh.rendered_models": "bigquery.sqlmesh.rendered_models",
}


def reset_local_duckdb(path: str):
    conn = duckdb.connect(path)
    response = conn.query("SHOW ALL TABLES")
    schema_names = response.df()["schema"].unique().tolist()
    for schema_name in schema_names:
        if not schema_name.startswith(DUCKDB_SOURCES_SCHEMA_PREFIX):
            logger.info(f"dropping schema {schema_name}")
            conn.query(f"DROP schema {schema_name} cascade")
