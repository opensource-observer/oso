import logging
from pathlib import Path
import urllib.request
import zipfile
import os
import subprocess
from google.cloud import bigquery as bq

from dagster._core.definitions.result import MaterializeResult
from dagster import asset, AssetExecutionContext, Definitions
from dagster_gcp import BigQueryResource
import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
if PROJECT_ID is None:
    raise Exception("Google project ID not found")

TEMP_DIR = '/tmp'

@asset(
    group_name="crypto_ecosystems"
)
def crypto_ecosystem_data(context: AssetExecutionContext, bigquery: BigQueryResource) -> MaterializeResult:
    zip_url = "https://github.com/electric-capital/crypto-ecosystems/archive/refs/heads/master.zip"
    zip_file = Path(TEMP_DIR) / "crypto-ecosystems.zip"

    context.log.info(f"Downloading repository from {zip_url}")

    urllib.request.urlretrieve(zip_url, zip_file)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(TEMP_DIR)

    repo_path = Path(TEMP_DIR) / "crypto-ecosystems-master"

    script_file = repo_path / "run.sh"
    os.chmod(script_file, 0o755)

    export_file = repo_path / "exports.jsonl"
    export_cmd = ["./run.sh", "export", str(export_file)]

    context.log.info("Generating JSONL file")
    subprocess.run(export_cmd)

    records = pd.read_json(export_file, lines=True)
    df = pd.DataFrame(records)
    context.log.info(f"{len(records)} records found in jsonl file")

    with bigquery.get_client() as client:
        job = client.load_table_from_dataframe(
            dataframe=df,
            destination=f"{PROJECT_ID}.crypto_ecosystems.crypto_ecosystems_data",
            job_config=bq.LoadJobConfig(
                write_disposition="WRITE_TRUNCATE", #Overwrite existing data
            )
        )
        job.result()

    context.log.info("Sucessfully uploaded dataset")

    return MaterializeResult(
        metadata={
            "records_exported":len(df),
            "exported_file_size": os.path.getsize(export_file),
            "sample_data": df.head(3).to_dict('records')
        }
    )

@asset(
    deps=[crypto_ecosystem_data],
    group_name="crypto_ecosystems"
)
def bitcoin_ecosystem_data(
    context,
    bigquery: BigQueryResource
) -> MaterializeResult:
    """
    Asset that filters for Bitcoin ecosystem data
    """

    sql_query = f"""
    SELECT * FROM {PROJECT_ID}.crypto_ecosystems.crypto_ecosystems_data WHERE LOWER(eco_name) LIKE %bitcoin%
    """

    job_config = bq.QueryJobConfig(destination = f"{PROJECT_ID}.crypto_ecosystems.bitcoin_ecosystem_data")
    with bigquery.get_client() as client:
        job = client.query(sql_query, job_config=job_config)
        result = job.result()

        context.log.info(f"Created Bitcoin ecosystem table with {result.total_rows} rows")

    return MaterializeResult(
        metadata={
            "sql_query": sql_query,
            "row_count": result.total_rows,
            "table_id": f"{PROJECT_ID}.crypto_ecosystems.bitcoin_ecosystem_data"
        }
    )

defs = Definitions(
    assets=[crypto_ecosystem_data, bitcoin_ecosystem_data],
    resources={
        "bigquery": BigQueryResource(
            project="",
            location=""
        )
    },
)
