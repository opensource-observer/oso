import logging
import typing as t

from oso_semantic import AttributePathTransformer
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

from .definition import (
    AttributePath,
    BoundDimension,
    BoundRelationship,
    Filter,
    JoinTree,
    Model,
    QueryComponent,
    QueryRegistry,
    Registry,
)
from .utils import exp_to_str

logger = logging.getLogger(__name__)


class QueryBuilder(QueryRegistry):
    def __init__(self, registry: Registry):
        self._registry = registry
        self._select_refs: list[AttributePath] = []
        self._references: list[AttributePath] = []
        self._root_model: Model | None = None

        self._select_parts: list[QueryComponent] = []
        self._select_aliases: list[str] = []
        self._filter_parts: list[QueryComponent] = []

        self._limit = 0

    def add_reference(self, reference: AttributePath):
        """Adds an attribute reference to the query

        Every reference adds 0 or more joins to the query
        """
        self._references.append(reference)

        return self

    def select(self, *selects: str):
        """Add a model attribute to the select clause"""
        for select in selects:
            result = AttributePathTransformer.transform(parse_one(select), registry=self._registry)
            print(f"Select result: {result.references}")
            print(f"Select node: {result.node}")
            reference = result.references[0]
            alias = reference.to_select_alias()
            if isinstance(result.node, exp.Alias):
                alias = exp_to_str(result.node.alias)

            # validate the select by checking the attribute references

            if not reference.is_valid_for_registry(self._registry):
                raise ValueError(f"Invalid reference {reference} for registry")
            part = reference.resolve(self._registry)

            for resolved_reference in part.resolved_references:
                if resolved_reference not in self._references:
                    self.add_reference(resolved_reference)
            self._select_parts.append(part)
            self._select_aliases.append(alias)
        return self

    def where(self, *filters: str):
        """Add a filter to the query"""
        for filter in filters:
            filter_expr = Filter(query=filter)
            traverser = AttributePath(path=[]).traverser()
            filter_part = filter_expr.to_query_component(
                traverser, filter_expr.query, self._registry
            )
            print(f"Filter part: {filter_part}")

            for ref in filter_part.resolved_references:
                self.add_reference(ref)

            self._filter_parts.append(filter_part)
        return self

    def add_limit(self, limit: int):
        """Add a limit to the query"""
        self._limit = limit
        return self

    def build(self):
        """Render a select query"""
        join_tree = self._registry.dag.find_best_join_tree(self._references)
        self._root_model = self._registry.get_model(join_tree.root)

        # Turn references into actual expressions
        select_parts = self._select_parts
        select_expressions: list[exp.Expression] = []
        group_by_expressions: list[str] = []

        for i in range(len(select_parts)):
            part = select_parts[i]
            select_expressions.append(part.expression.as_(self._select_aliases[i]))

            if not part.is_aggregate:
                group_by_expressions.append(str(i + 1))

        # Establish base query
        query = exp.select(*select_expressions)

        base_model = self._root_model
        base_table = base_model.table_exp.as_(
            AttributePath.from_string("").traverser().alias(base_model.name)
        )  # Use an empty path to get the root model alias
        query = query.from_(base_table)

        # Add joins
        joiner = QueryJoiner(query, base_model, join_tree, self._registry)
        for ref in sorted(
            self._references, key=lambda r: join_tree.depths[r.base_model]
        ):
            joiner.join_reference(ref)

        query = joiner.joined_query

        # Add filters
        for part in self._filter_parts:
            part_expression = part.expression

            query = query.where(part_expression)

        # Apply appropriate group by
        if group_by_expressions:
            query = query.group_by(*group_by_expressions)

        if self._limit:
            query = query.limit(self._limit)

        # Replace $SEMANTIC_REF anonymous functions. The reason we do this here
        # right now is because it seems we will likely need to split the query
        # into multiple queries depending on the models joined. Doing a late
        # resolution of the actual column names allows us to do this on a per
        # subquery basis. For now, this isn't implemeneted.
        def transform_semantic_ref(node: exp.Expression):
            if (
                isinstance(node, exp.Anonymous)
                and exp_to_str(node.this).lower() == "$semantic_ref"
            ):
                # We need to replace the function with the actual column name
                # from the registry
                semantic_ref = exp_to_str(node.expressions[0])
                ref = AttributePath.from_string(semantic_ref)
                # Hack for now we should replace with a lookup in this instance
                traverser = ref.traverser()
                while traverser.next():
                    pass
                return f"{traverser.current_model_name}.{traverser.current_attribute_name}"
            return node

        query = query.transform(transform_semantic_ref)

        return query


class QueryJoiner:
    def __init__(
        self,
        select: exp.Select,
        base_model: Model,
        join_tree: JoinTree,
        registry: Registry,
        dialect: str = "duckdb",
    ):
        self._select = select
        self._base_model = base_model
        self._registry = registry
        self._join_tree = join_tree
        self._already_joined: set[str] = set()
        self._already_joined.add(base_model.name)
        self._dialect = dialect

    def join_reference(self, reference: AttributePath):
        """Join the reference to the current base model"""
        traverser = reference.traverser()

        if self._base_model.name != reference.base_model:
            # Join to the base_model
            self._join(
                from_model_name=self._base_model.name,
                from_table_alias=traverser.alias(self._base_model.name),
                to_model_name=reference.base_model,
                create_alias=traverser.alias,
            )

        from_model_name = reference.base_model
        from_table_alias = traverser.alias(reference.base_model)
        from_table_through_attribute = traverser.current_attribute_name

        while traverser.next():
            self._join(
                from_model_name=from_model_name,
                from_table_alias=from_table_alias,
                to_model_name=traverser.current_model_name,
                create_alias=traverser.alias,
                through_attribute=from_table_through_attribute,
            )

            from_model_name = traverser.current_model_name
            from_table_alias = traverser.alias(from_model_name)
            from_table_through_attribute = traverser.current_attribute_name

    def _join(
        self,
        *,
        from_model_name: str,
        from_table_alias: str,
        to_model_name: str,
        create_alias: t.Callable[[str], str] = lambda x: x,
        through_attribute: str = "",
    ):
        logger.debug(
            f"Joining `{from_model_name}` to `{to_model_name}` through `{through_attribute}`"
        )
        registry = self._registry
        query = self._select

        join_path = self._join_relationships(
            from_model_name, to_model_name, through_attribute=through_attribute
        )

        logger.debug(f"Join path: {join_path}")

        for relationship in join_path:
            referenced_model = registry.get_model(relationship.ref_model)
            referenced_model_alias = create_alias(relationship.ref_model)

            referenced_model_table = referenced_model.table_exp.as_(
                referenced_model_alias
            )

            if referenced_model_alias in self._already_joined:
                continue

            query = query.join(
                referenced_model_table,
                on=" AND ".join(
                    [
                        f"{from_table_alias}.{exp.to_identifier(source_foreign_key)} = {referenced_model_alias}.{exp.to_identifier(ref_key)}"
                        for source_foreign_key, ref_key in zip(
                            relationship.source_foreign_key,
                            relationship.ref_key,
                        )
                    ]
                ),
                join_type="left",
            )

            from_table_alias = referenced_model_alias
            from_model_name = referenced_model.name

            self._already_joined.add(referenced_model_alias)
        self._select = query

    def _join_relationships(
        self, from_model: str, to_model: str, through_attribute: str = ""
    ) -> t.List[BoundRelationship]:
        """Returns the join path between two models"""
        path = self._join_tree.get_path(from_model, to_model)

        def build_join_path(
            model_path: t.List[str], via_attribute: str = ""
        ) -> t.List[BoundRelationship]:
            prev_model: Model | None = None
            join_path: t.List[BoundRelationship] = []
            for model_name in model_path:
                if prev_model is None:
                    via_attribute = via_attribute
                    prev_model = self._registry.models[model_name]
                    continue

                relationship = prev_model.find_relationship(
                    name=via_attribute, model_ref=model_name
                )
                prev_model = self._registry.models[model_name]
                join_path.append(relationship)
            return join_path

        return build_join_path(path, through_attribute)

    @property
    def joined_query(self):
        return self._select
