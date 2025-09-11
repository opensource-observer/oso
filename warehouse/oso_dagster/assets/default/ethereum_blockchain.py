from datetime import datetime

import dagster as dg
from oso_dagster.config import DagsterConfig
from oso_dagster.factories import dlt_factory
from oso_dagster.factories.cryo import CryoResourceConfig, cryo_resource_factory

ETHEREUM_START_DATE = datetime.strptime("2015-07-30", "%Y-%m-%d")
ETHEREUM_PARTITION = dg.DailyPartitionsDefinition(start_date=ETHEREUM_START_DATE)


@dlt_factory(key_prefix="ethereum", name="blocks", partitions_def=ETHEREUM_PARTITION)
def ethereum_blocks(
    context: dg.AssetExecutionContext,
    global_config: DagsterConfig,
):
    yield cryo_resource_factory(
        global_config,
        CryoResourceConfig(
            datatype="blocks",
            rpc_url=global_config.ethereum_rpc_url,
            primary_key=["block_number"],
            start_date=ETHEREUM_START_DATE,
            partition_date=datetime.strptime(context.partition_key, "%Y-%m-%d"),
            partition_key="dt",
        ),
    )


@dlt_factory(
    key_prefix="ethereum", name="transactions", partitions_def=ETHEREUM_PARTITION
)
def ethereum_transactions(
    context: dg.AssetExecutionContext,
    global_config: DagsterConfig,
):
    yield cryo_resource_factory(
        global_config,
        CryoResourceConfig(
            datatype="transactions",
            rpc_url=global_config.ethereum_rpc_url,
            primary_key=["block_number", "transaction_index"],
            start_date=ETHEREUM_START_DATE,
            partition_date=datetime.strptime(context.partition_key, "%Y-%m-%d"),
            partition_key="dt",
        ),
    )


@dlt_factory(key_prefix="ethereum", name="logs", partitions_def=ETHEREUM_PARTITION)
def ethereum_logs(
    context: dg.AssetExecutionContext,
    global_config: DagsterConfig,
):
    yield cryo_resource_factory(
        global_config,
        CryoResourceConfig(
            datatype="logs",
            rpc_url=global_config.ethereum_rpc_url,
            primary_key=["block_number", "log_index"],
            start_date=ETHEREUM_START_DATE,
            partition_date=datetime.strptime(context.partition_key, "%Y-%m-%d"),
            partition_key="dt",
        ),
    )


@dlt_factory(key_prefix="ethereum", name="traces", partitions_def=ETHEREUM_PARTITION)
def ethereum_traces(
    context: dg.AssetExecutionContext,
    global_config: DagsterConfig,
):
    yield cryo_resource_factory(
        global_config,
        CryoResourceConfig(
            datatype="traces",
            rpc_url=global_config.ethereum_rpc_url,
            primary_key=["block_number", "transaction_index", "trace_address"],
            start_date=ETHEREUM_START_DATE,
            partition_date=datetime.strptime(context.partition_key, "%Y-%m-%d"),
            partition_key="dt",
        ),
    )
