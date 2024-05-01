# CBT - cheap build tool (only works for bigquery)
#
# A poor excuse for a dbt replacement when calling sql as a library
from typing import List

from dagster import ConfigurableResource, InitResourceContext
from dagster_gcp import BigQueryResource
from google.cloud.bigquery import TableReference, QueryJobConfig, TimePartitioning
from jinja2 import Environment, FileSystemLoader, select_autoescape, meta
from .bq import BigQueryTableQueryHelper


class MissingVars(Exception):
    def __init__(self, missing_vars: List[str]):
        missing_vars_str = ", ".join(missing_vars)
        super(MissingVars, self).__init__(
            f"CBT rendering is missing vars: {missing_vars_str}"
        )


class CBT:
    def __init__(self, bigquery: BigQueryResource, search_paths: List[str]):
        self.bigquery = bigquery
        loader = FileSystemLoader(search_paths)
        self.env = Environment(
            loader=loader,
        )
        self.env.globals["source"] = self.load_source_table

    def run_model(
        self,
        model_file: str,
        destination_table: TableReference,
        time_partitioning_column: str = "",
        **vars,
    ):
        select_query = self.render_model(model_file=model_file, **vars)
        with self.bigquery.get_client() as client:
            job_config = QueryJobConfig(
                destination=destination_table,
            )
            if time_partitioning_column:
                time_partitioning = TimePartitioning(field=time_partitioning_column)
                job_config["time_partitioning"] = time_partitioning

            job = client.query(select_query, job_config=job_config)
            job.result()

    def render_model(self, model_file: str, **vars):
        model_source = self.env.loader.get_source(self.env, model_file)
        ast = self.env.parse(model_source)
        expected_vars = meta.find_undeclared_variables(ast)
        declared_vars = set(vars.keys())
        missing_vars = expected_vars - declared_vars
        if len(missing_vars) > 0:
            raise MissingVars(list(missing_vars))
        return self.env.get_template(model_file).render(**vars)

    def load_source_table(self, name: str):
        with self.bigquery.get_client() as client:
            return BigQueryTableQueryHelper.load_by_table(client, name)


class CBTResource(ConfigurableResource):
    bigquery: BigQueryResource
    search_paths: List[str]

    def get(self) -> CBT:
        return CBT(bigquery=self.bigquery, search_paths=self.search_paths)
