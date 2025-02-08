# CBT - cheap build tool (only works for bigquery)
#
# A poor excuse for a dbt replacement when calling sql as a library
import os
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import List, Optional, Sequence

import arrow
from dagster import ConfigurableResource, DagsterLogManager
from dagster_gcp import BigQueryResource
from google.cloud.bigquery import Client, TableReference
from google.cloud.exceptions import NotFound
from jinja2 import Environment, FileSystemLoader, meta

from .bq import BigQueryConnector, BigQueryTableQueryHelper
from .context import ContextQuery, DataContext, Transformation


class UpdateStrategy(Enum):
    REPLACE = 0
    APPEND = 1
    MERGE = 2
    REPLACE_PARTITIONS = 3


@dataclass
class TimePartitioning:
    column: str
    type: str


@dataclass
class TimeRange:
    start: arrow.Arrow
    end: arrow.Arrow


class MissingVars(Exception):
    def __init__(self, missing_vars: List[str]):
        missing_vars_str = ", ".join(missing_vars)
        super(MissingVars, self).__init__(
            f"CBT rendering is missing vars: {missing_vars_str}"
        )


class CBT:
    def __init__(
        self,
        log: DagsterLogManager,
        bigquery: BigQueryResource,
        search_paths: List[str],
    ):
        self.bigquery = bigquery
        self.search_paths = [
            os.path.join(os.path.abspath(os.path.dirname(__file__)), "operations"),
        ]
        self.add_search_paths(search_paths)

        self.log = log
        self.load_env()

    def load_env(self):
        loader = FileSystemLoader(self.search_paths)
        self.env = Environment(
            loader=loader,
        )

    def add_search_paths(self, search_paths: List[str]):
        for p in search_paths:
            if p not in self.search_paths:
                self.search_paths.append(p)
        self.load_env()

    def query_with_string(self, query_str: str, timeout: float = 300):
        with self.bigquery.get_client() as client:
            job = client.query(query_str, timeout=timeout)
            return job.result()

    def query(self, model_file: str, timeout: float = 300, **vars):
        rendered = self.render_model(model_file, **vars)
        return self.query_with_string(rendered, timeout)

    # we should transition to this instead of using jinja
    def query_with_sqlglot(
        self,
        query: ContextQuery,
        transformations: Optional[Sequence[Transformation]] = None,
    ):
        with self.bigquery.get_client() as client:
            connector = BigQueryConnector(client)
            context = DataContext(connector)
            return context.execute_query(query, transformations)

    def hybrid_query(
        self,
        model_file: str,
        transformations: Optional[Sequence[Transformation]] = None,
        **vars,
    ):
        with self.bigquery.get_client() as client:
            rendered = self.render_model(model_file, **vars)
            self.log.debug(rendered)
            connector = BigQueryConnector(client)
            context = DataContext(connector)
            return context.execute_query(rendered, transformations)

    def hybrid_render(
        self,
        model_file: str,
        transformations: Optional[Sequence[Transformation]] = None,
        **vars,
    ):
        pass

    def hybrid_transform(
        self,
        model_file: str,
        destination_table: str | TableReference,
        update_strategy: UpdateStrategy = UpdateStrategy.APPEND,
        transformations: Optional[Sequence[Transformation]] = None,
        time_partitioning: Optional[TimePartitioning] = None,
        unique_column: Optional[str] = None,
        timeout: float = 300,
        dry_run: bool = False,
        **vars,
    ):
        with self.bigquery.get_client() as client:
            table_exists = True
            try:
                client.get_table(destination_table)
            except NotFound:
                table_exists = False

            if update_strategy == UpdateStrategy.REPLACE or not table_exists:
                return self._transform_replace(
                    client,
                    model_file,
                    destination_table,
                    transformations=transformations,
                    time_partitioning=time_partitioning,
                    unique_column=unique_column,
                    timeout=timeout,
                    dry_run=dry_run,
                    **vars,
                )
            return self._transform_existing(
                client,
                model_file,
                destination_table,
                update_strategy,
                transformations=transformations,
                time_partitioning=time_partitioning,
                unique_column=unique_column,
                timeout=timeout,
                dry_run=dry_run,
                **vars,
            )

    def transform(
        self,
        model_file: str,
        destination_table: str | TableReference,
        update_strategy: UpdateStrategy = UpdateStrategy.REPLACE,
        time_partitioning: Optional[TimePartitioning] = None,
        unique_column: Optional[str] = None,
        timeout: float = 300,
        dry_run: bool = False,
        **vars,
    ):
        with self.bigquery.get_client() as client:
            table_exists = True
            try:
                client.get_table(destination_table)
            except NotFound:
                table_exists = False

            if update_strategy == UpdateStrategy.REPLACE or not table_exists:
                return self._transform_replace(
                    client,
                    model_file,
                    destination_table,
                    time_partitioning=time_partitioning,
                    unique_column=unique_column,
                    timeout=timeout,
                    dry_run=dry_run,
                    **vars,
                )
            return self._transform_existing(
                client,
                model_file,
                destination_table,
                update_strategy,
                time_partitioning=time_partitioning,
                unique_column=unique_column,
                timeout=timeout,
                dry_run=dry_run,
                **vars,
            )

    def _transform_existing(
        self,
        client: Client,
        model_file: str,
        destination_table: str | TableReference,
        update_strategy: UpdateStrategy,
        transformations: Optional[Sequence[Transformation]] = None,
        time_partitioning: Optional[TimePartitioning] = None,
        unique_column: Optional[str] = None,
        timeout: float = 300,
        dry_run: bool = False,
        **vars,
    ):
        select_query = self.render_model(
            model_file=model_file, unique_column=unique_column, **vars
        )

        source_table_fqn = None
        if "source_table_fqn" in vars:
            source_table_fqn = vars["source_table_fqn"]

        if transformations:
            connector = BigQueryConnector(client)
            context = DataContext(connector)
            select_query = context.transform_query(select_query, transformations).sql(
                dialect="bigquery"
            )
            self.log.debug(select_query)

        update_query = self.render_model(
            "_cbt_append.sql",
            select_query=select_query,
            destination_table=destination_table,
            time_partitioning=time_partitioning,
        )
        time_range = None
        if update_strategy == UpdateStrategy.MERGE:
            self.log.debug("Using merge strategy")
            if time_partitioning:
                time_range_query = self.render_model(
                    "_cbt_time_range.sql",
                    select_query=select_query,
                    destination_table=destination_table,
                    unique_column=unique_column,
                    time_partitioning=time_partitioning,
                )
                self.log.debug(
                    {"message": "getting time range", "query": time_range_query}
                )
                job = client.query(time_range_query, timeout=timeout)
                time_range_row_iter = job.result()
                time_range_rows = list(time_range_row_iter)
                if len(time_range_rows) != 1:
                    raise Exception("time column might be wrong")
                time_range = TimeRange(
                    arrow.get(time_range_rows[0].start),
                    arrow.get(time_range_rows[0].end),
                )
                self.log.debug(
                    {
                        "message": "time range for update",
                        "start": time_range.start,
                        "end": time_range.end,
                    }
                )

            if not unique_column:
                raise Exception(
                    "UpdatedStrategy.MERGE strategy requires a unique field"
                )
            update_query = self.render_model(
                "_cbt_merge.sql",
                select_query=select_query,
                destination_table=destination_table,
                unique_column=unique_column,
                time_partitioning=time_partitioning,
                time_range=time_range,
                source_table_fqn=source_table_fqn,
            )
            self.log.debug({"message": "rendering merge query", "query": update_query})

        if not dry_run:
            self.log.debug({"message": "updating", "query": update_query})
            job = client.query(update_query, timeout=timeout)
            job.result()
        else:
            self.log.debug(f"dry_run: {update_query}")

    def _transform_replace(
        self,
        client: Client,
        model_file: str,
        destination_table: str | TableReference,
        time_partitioning: Optional[TimePartitioning] = None,
        transformations: Optional[Sequence[Transformation]] = None,
        unique_column: Optional[str] = None,
        timeout: float = 300,
        dry_run: bool = False,
        **vars,
    ):
        select_query = self.render_model(
            model_file=model_file, unique_column=unique_column, **vars
        )
        if transformations:
            connector = BigQueryConnector(client)
            context = DataContext(connector)
            select_query = context.transform_query(select_query, transformations).sql(
                dialect="bigquery"
            )

        if time_partitioning:
            self.log.debug("creating table with a time partition")
        create_or_replace_query = self.render_model(
            "_cbt_replace.sql",
            destination_table=destination_table,
            time_partitioning=time_partitioning,
            unique_column=unique_column,
            select_query=select_query,
        )
        if not dry_run:
            job = client.query(create_or_replace_query, timeout=timeout)
            self.log.debug(
                {"message": "replacing with query", "query": create_or_replace_query}
            )
            job.result()
        else:
            self.log.debug(f"dry_run: {create_or_replace_query}")

    def _transform_replace_partition(
        self,
        client: Client,
        model_file: str,
        destination_table: str | TableReference,
        time_partitioning: Optional[TimePartitioning] = None,
        transformations: Optional[Sequence[Transformation]] = None,
        unique_column: Optional[str] = None,
        timeout: float = 300,
        dry_run: bool = False,
        **vars,
    ):
        select_query = self.render_model(
            model_file=model_file, unique_column=unique_column, **vars
        )
        if transformations:
            connector = BigQueryConnector(client)
            context = DataContext(connector)
            select_query = context.transform_query(select_query, transformations).sql(
                dialect="bigquery"
            )

        if not time_partitioning:
            raise Exception(
                "time partitioning is required for a REPLACE_PARTITIONS update"
            )
        replace_partition_query = self.render_model(
            "_cbt_replace_partition.sql",
            destination_table=destination_table,
            time_partitioning=time_partitioning,
            unique_column=unique_column,
            select_query=select_query,
        )

        if not dry_run:
            job = client.query(replace_partition_query, timeout=timeout)
            self.log.debug(
                {
                    "message": "replacing partitions with query",
                    "query": replace_partition_query,
                }
            )
            job.result()
        else:
            self.log.debug(f"dry_run: {replace_partition_query}")

    def render_model(self, model_file: str, **vars):
        assert self.env.loader
        model_source, _, _ = self.env.loader.get_source(self.env, model_file)
        ast = self.env.parse(model_source)
        expected_vars = meta.find_undeclared_variables(ast)
        declared_vars = set(vars.keys())
        declared_vars.add("source")
        missing_vars = expected_vars - declared_vars
        if len(missing_vars) > 0:
            self.log.warn(
                "potentially missing variables",
                exc_info=MissingVars(list(missing_vars)),
            )
        return self.env.get_template(model_file).render(
            source=SourceTableLoader(self.bigquery), **vars
        )

    def load_source_table(self, name: str):
        with self.bigquery.get_client() as client:
            return BigQueryTableQueryHelper.load_by_table(client, name)


class SourceTableLoader:
    def __init__(self, bigquery: BigQueryResource):
        self.bigquery = bigquery

    @cache
    def __call__(self, name: str):
        with self.bigquery.get_client() as client:
            return BigQueryTableQueryHelper.load_by_table(client, name)


class CBTResource(ConfigurableResource):
    bigquery: BigQueryResource
    search_paths: List[str]

    def get(self, log: DagsterLogManager) -> CBT:
        return CBT(log, bigquery=self.bigquery, search_paths=self.search_paths)
