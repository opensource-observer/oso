# CBT - cheap build tool (only works for bigquery)
#
# A poor excuse for a dbt replacement when calling sql as a library
from dagster_gcp import BigQueryResource
from google.cloud.bigquery import TableReference
from jinja2 import Environment, FileSystemLoader, select_autoescape


class CBT:
    def __init__(self, bigquery: BigQueryResource, search_paths: List[str]):
        self.bigquery = bigquery
        loader = FileSystemLoader(search_paths)
        self.env = Environment(
            loader=loader,
        )

    def run_load(
        self, query_file: str, destination_table: TableReference, *args, **kwargs
    ):
        select_query_template = self.env.get_template(query_file)
        select_query = select_query_template.render(*args, **kwargs)
        with self.bigquery.get_client() as client:
            job = client.query(select_query)
            job.destination(destination_table)
            job.result()
