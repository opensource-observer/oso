import datetime as dt
import pathlib

import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, asset
from sqlalchemy import create_engine, text

from warehouse.oso_dagster.utils.secrets import SecretReference


@asset(group_name="db_replication", required_resource_keys={"secret_resolver"})
def replicate_postgres_orders(context: AssetExecutionContext) -> str:
    uri = context.resources.secret_resolver.resolve_as_str(
        SecretReference(group_name="postgres", key="uri")
    )
    since = context.resources.secret_resolver.resolve_as_str(
        SecretReference(group_name="postgres", key="since")
    )
    eng = create_engine(uri)
    df = pd.read_sql(
        text("select * from orders where updated_at >= :since"),
        eng,
        params={"since": since},
    )

    out = pathlib.Path("warehouse/oso_dagster/tmp/postgres/orders")
    out.mkdir(parents=True, exist_ok=True)
    fp = out / f"{dt.date.today().isoformat()}.parquet"
    df.to_parquet(fp, index=False)

    context.add_output_metadata(
        {
            "rows": MetadataValue.int(len(df)),
            "path": MetadataValue.path(str(fp)),
        }
    )
    return str(fp)
