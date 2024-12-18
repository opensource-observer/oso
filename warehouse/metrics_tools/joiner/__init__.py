import typing as t

from metrics_tools.transformer import SQLTransformer, Transform
from sqlglot import exp


class JoinerTransform(Transform):
    def __init__(self, entity_type: str, timeseries_sources: t.List[str]):
        self._entity_type = entity_type
        self._timeseries_sources = timeseries_sources

    def __call__(self, query: t.List[exp.Expression]) -> t.List[exp.Expression]:
        entity_type = self._entity_type
        if entity_type == "artifact":
            return query

        def _transform(node: exp.Expression):
            if not isinstance(node, exp.Select):
                return node
            select = node

            # Check if this using the timeseries source tables as a join or the from
            is_using_timeseries_source = False
            for table in select.find_all(exp.Table):
                if table.this.this in self._timeseries_sources:
                    is_using_timeseries_source = True
            if not is_using_timeseries_source:
                return node

            for i in range(len(select.expressions)):
                ex = select.expressions[i]
                if not isinstance(ex, exp.Alias):
                    continue

                # If to_artifact_id is being aggregated then it's time to rewrite
                if isinstance(ex.this, exp.Column) and isinstance(
                    ex.this.this, exp.Identifier
                ):
                    if ex.this.this.this == "to_artifact_id":
                        updated_select = select.copy()
                        current_from = t.cast(exp.From, updated_select.args.get("from"))
                        assert isinstance(current_from.this, exp.Table)
                        current_table = current_from.this
                        current_alias = current_table.alias

                        # Add a join to this select
                        updated_select = updated_select.join(
                            exp.Table(
                                this=exp.to_identifier("artifacts_by_project_v1"),
                                db=exp.to_identifier("metrics"),
                            ),
                            on=f"{current_alias}.to_artifact_id = artifacts_by_project_v1.artifact_id",
                            join_type="inner",
                        )

                        new_to_entity_id_col = exp.to_column(
                            "artifacts_by_project_v1.project_id", quoted=True
                        )
                        new_to_entity_alias = exp.to_identifier(
                            "to_project_id", quoted=True
                        )

                        if entity_type == "collection":
                            updated_select = updated_select.join(
                                exp.Table(
                                    this=exp.to_identifier("projects_by_collection_v1"),
                                    db=exp.to_identifier("metrics"),
                                ),
                                on="artifacts_by_project_v1.project_id = projects_by_collection_v1.project_id",
                                join_type="inner",
                            )

                            new_to_entity_id_col = exp.to_column(
                                "projects_by_collection_v1.collection_id", quoted=True
                            )
                            new_to_entity_alias = exp.to_identifier(
                                "to_collection_id", quoted=True
                            )

                        # replace the select and the grouping with the project id in the joined table
                        to_artifact_id_col_sel = t.cast(
                            exp.Alias, updated_select.expressions[i]
                        )
                        current_to_artifact_id_col = t.cast(
                            exp.Column, to_artifact_id_col_sel.this
                        )

                        to_artifact_id_col_sel.replace(
                            exp.alias_(
                                new_to_entity_id_col,
                                alias=new_to_entity_alias,
                            )
                        )

                        group_exp = updated_select.args.get("group")
                        if group_exp:
                            group = t.cast(exp.Group, group_exp)
                            for group_idx in range(len(group.expressions)):
                                group_col = t.cast(
                                    exp.Column, group.expressions[group_idx]
                                )
                                if group_col == current_to_artifact_id_col:
                                    group_col.replace(new_to_entity_id_col)

                        return updated_select
            # If nothing happens in the for loop then we didn't find the kind of
            # expected select statement
            return node

        return list(map(lambda expression: expression.transform(_transform), query))


def joiner_transform(
    query: str,
    entity_type: str,
    timeseries_sources: t.List[str],
    rolling_window: t.Optional[int] = None,
    rolling_unit: t.Optional[str] = None,
    time_aggregation: t.Optional[str] = None,
):
    if entity_type == "artifact":
        return SQLTransformer(transforms=[]).transform(query)
    transformer = SQLTransformer(
        transforms=[
            # Semantic transform
            JoinerTransform(entity_type, timeseries_sources)
        ]
    )
    return transformer.transform(query)
