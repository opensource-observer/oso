from __future__ import annotations

import typing as t

from sqlmesh import CustomMaterialization, Model
from sqlmesh.core.engine_adapter._typing import QueryOrDF


class MetricsIncrementalMaterialization(CustomMaterialization):
    NAME = "metrics_incremental"

    def insert(
        self,
        table_name: str,
        query_or_df: QueryOrDF,
        model: Model,
        is_first_insert: bool,
        **kwargs: t.Any,
    ) -> None:
        # We need to do some kind of query that is insert only even if it's incremental.
        assert model.time_column
        self.adapter.insert_overwrite_by_time_partition(
            table_name,
            query_or_df,
            time_formatter=model.convert_to_time_column,
            time_column=model.time_column,
            columns_to_types=model.columns_to_types,
            **kwargs,
        )

        self._replace_query_for_model(model, table_name, query_or_df)
