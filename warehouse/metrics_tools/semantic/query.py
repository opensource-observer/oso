import logging
import typing as t

from metrics_tools.utils.glot import exp_to_str
from sqlglot import exp

from .definition import AttributePath, Filter, Model, QueryPart, Registry

logger = logging.getLogger(__name__)


class QueryBuilder:
    def __init__(self, registry: Registry):
        self._registry = registry
        self._select_refs: list[AttributePath] = []
        self._references: list[AttributePath] = []
        self._deepest_reference: AttributePath | None = None

        self._select_parts: list[QueryPart] = []
        self._select_aliases: list[str] = []
        self._filter_parts: list[QueryPart] = []

        self._limit = 0

    def add_reference(self, reference: AttributePath):
        """Adds an attribute reference to the query

        Every reference adds 0 or more joins to the query
        """
        self._references.append(reference)

        if self._deepest_reference is None:
            self._deepest_reference = reference
        else:
            ref_depth = self._registry.dag.get_ancestor_depth(reference.base_model)
            deepest_ref_depth = self._registry.dag.get_ancestor_depth(
                self._deepest_reference.base_model
            )
            if ref_depth > deepest_ref_depth:
                self._deepest_reference = reference

        return self

    def add_select(self, reference: AttributePath, alias: str):
        """Add a model attribute to the select clause"""
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

    def add_filter(self, filter: Filter):
        """Add a filter to the query"""

        traverser = AttributePath(path=[]).traverser()
        filter_part = filter.to_query_part(traverser, filter.query, self._registry)

        for ref in filter_part.resolved_references:
            self.add_reference(ref)

        self._filter_parts.append(filter_part)
        return self

    def add_limit(self, limit: int):
        """Add a limit to the query"""
        self._limit = limit
        return self

    @property
    def base_model(self):
        """Get the base model of the query"""
        if not self._deepest_reference:
            raise ValueError("No reference added to the query")
        return self._registry.get_model(self._deepest_reference.base_model)

    def build(self):
        """Render a select query"""

        if not self._deepest_reference:
            raise ValueError("No reference added to the query")

        base_model = self.base_model
        deepest_reference = self._deepest_reference

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

        base_table = base_model.table_exp
        base_table_with_alias = base_table.as_(
            deepest_reference.traverser().alias(base_model.name)
        )
        query = query.from_(base_table_with_alias)

        # Add joins
        joiner = QueryJoiner(query, base_model, self._registry)
        for ref in self._references:
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
            if isinstance(node, exp.Anonymous) and exp_to_str(node.this).lower() == "$semantic_ref":
                # We need to replace the function with the actual column name
                # from the registry
                semantic_ref = exp_to_str(node.expressions[0])
                ref = AttributePath.from_string(semantic_ref)
                # Hack for now we should replace with a lookup in this instance
                traverser = ref.traverser()
                while traverser.next():
                    pass
                return exp.to_column(f"{traverser.current_table_alias}.{traverser.current_attribute_name}")
            return node
        query = query.transform(transform_semantic_ref)

        return query


class QueryJoiner:
    def __init__(self, select: exp.Select, base_model: Model, registry: Registry, dialect: str = "duckdb"):
        self._select = select
        self._base_model = base_model
        self._registry = registry
        self._already_joined: set[str] = set()
        self._already_joined.add(base_model.name)
        self._dialect = dialect

    def join_reference(self, reference: AttributePath):
        """Join the reference to the current base model"""
        traverser = reference.traverser()

        if self._base_model.name != reference.base_model:
            # Join to the base_model
            self.join(
                from_model_name=self._base_model.name,
                from_table_alias=traverser.alias(self._base_model.name),
                to_model_name=reference.base_model,
                create_alias=traverser.alias,
            )

        from_model_name = reference.base_model
        from_table_alias = traverser.alias(reference.base_model)
        from_table_through_attribute = traverser.current_attribute_name

        while traverser.next():
            self.join(
                from_model_name=from_model_name,
                from_table_alias=from_table_alias,
                to_model_name=traverser.current_model_name,
                create_alias=traverser.alias,
                through_attribute=from_table_through_attribute,
            )

            from_model_name = traverser.current_model_name
            from_table_alias = traverser.alias(from_model_name)
            from_table_through_attribute = traverser.current_attribute_name

    def join(
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

        join_path = registry.join_relationships(
            from_model_name, to_model_name, through_attribute=through_attribute
        )
        from_model = registry.get_model(from_model_name)

        logger.debug(f"Join path: {join_path}")

        for relationship in join_path:
            referenced_model = registry.get_model(relationship.model_ref)
            referenced_model_alias = create_alias(relationship.model_ref)

            referenced_model_table = referenced_model.table_exp.as_(
                referenced_model_alias
            )

            if referenced_model_alias in self._already_joined:
                continue

            if relationship.join_table:
                join_table = exp.to_table(relationship.join_table)
                join_table_alias = create_alias(join_table.name)
                join_table = join_table.as_(join_table_alias)

                from_model_primary_key = from_model.primary_key_expression(from_table_alias)
                join_table_self_key = relationship.self_key_with_alias(join_table_alias)
                join_table_foreign_key = relationship.foreign_key_with_alias(join_table_alias)
                referenced_model_primary_key = referenced_model.primary_key_expression(referenced_model_alias)


                query = query.join(
                    join_table,
                    on=f"{from_model_primary_key.sql(dialect=self._dialect)} = {join_table_self_key.sql(dialect=self._dialect)}",
                    join_type="left",
                )
                query = query.join(
                    referenced_model_table,
                    on=f"{join_table_foreign_key.sql(dialect=self._dialect)} = {referenced_model_primary_key.sql(dialect=self._dialect)}",
                    join_type="left",
                )
            else:
                query = query.join(
                    referenced_model_table,
                    on=f"{from_table_alias}.{relationship.foreign_key_column} = {referenced_model_alias}.{referenced_model.primary_key}",
                    join_type="left",
                )

            from_table_alias = referenced_model_alias
            from_model_name = referenced_model.name
            from_model = referenced_model

            self._already_joined.add(referenced_model_alias)
        self._select = query

    @property
    def joined_query(self):
        return self._select
