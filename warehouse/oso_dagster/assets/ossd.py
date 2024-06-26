from dagster import multi_asset, Output, AssetOut, AssetExecutionContext
from ossdirectory import fetch_data
import polars as pl


@multi_asset(
    outs={
        "projects": AssetOut(is_required=False, key_prefix="ossd"),
        "collections": AssetOut(is_required=False, key_prefix="ossd"),
    },
    can_subset=True,
)
def ossdirectory_repo(context: AssetExecutionContext):
    data = fetch_data()
    for output in context.op_execution_context.selected_output_names:
        yield Output(pl.from_dicts(getattr(data, output)), output)
