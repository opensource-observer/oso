import typing as t
from dataclasses import dataclass

from sqlglot import exp
from sqlmesh.core.dialect import MacroFunc

from .definition import AttributeReference, Model, Registry


def is_expression_attribute_reference(node: exp.Expression) -> bool:
    if isinstance(node, exp.Column):
        return True

    if not isinstance(node, exp.JSONExtract):
        return False

    base = node.this
    to = node.expression
    if not isinstance(base, (exp.Column, exp.Dot)):
        return False

    if not isinstance(to, (exp.Column, exp.JSONExtract)):
        return False

    if isinstance(to, exp.JSONExtract):
        return is_expression_attribute_reference(to)
    return True


@dataclass
class AttributeTransformerResult:
    """Internal result only used for the attribute reference transformer"""
    node: exp.Expression
    references: list[AttributeReference]


class AttributeReferenceTransformer:
    """Provides a transformer that tracks attribute references in an expression
    and replaces them with macro functions that can be resolved at sql
    generation time

    Should be called with the `transform` class method.
    """

    @classmethod
    def transform(cls, node: exp.Expression):
        """Transform an expression and return a result that also contains the
        attribute references found in the expression"""

        transformer = cls()
        transformed_node = node.transform(transformer)
        return AttributeTransformerResult(
            node=transformed_node, references=transformer.references
        )

    def __init__(self):
        self.references: list[AttributeReference] = []

    def __call__(self, node: exp.Expression):
        if is_expression_attribute_reference(node):
            if isinstance(node, exp.Column):
                raw_refs = [node.sql(dialect="duckdb")]
            else:
                raw_refs = [r for r in node.sql(dialect="duckdb").split("->")]

            self.references.append(AttributeReference(ref=raw_refs))
            refs_as_literals = [exp.Literal.string(r) for r in raw_refs]
            return MacroFunc(
                this=exp.Anonymous(
                    this="semantic_column_resolve", expressions=refs_as_literals
                )
            )
        return node


class FilterNode:
    @classmethod
    def from_expression(cls, node: exp.Expression):
        # We replace all attribute references with macro functions to lazily
        # evaluate the correct column name at sql generation time
        result = AttributeReferenceTransformer.transform(node)
        return cls(result.node, result.references)

    def __init__(
        self, expression: exp.Expression, references: list[AttributeReference]
    ):
        self.expression = expression
        self.references = references

    def resolve(self, registry: Registry):
        # We need to figure out if the reference is a dimension or metric
        # If it's a dimension it's a "where" clause
        # If it's a metrics we need it to be a "having" clause
        pass


class QueryBuilder:
    def __init__(self, registry: Registry):
        self._registry = registry
        self._select_refs: list[AttributeReference] = []
        self._references: list[AttributeReference] = []
        self._filter_nodes: list[FilterNode] = []
        self._deepest_reference: AttributeReference | None = None
        self._limit = 0

    def add_reference(self, reference: AttributeReference):
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

    def add_select(self, select: AttributeReference):
        """Add a model attribute to the select clause"""
        self.add_reference(select)
        return self

    def add_filter(self, filter: exp.Expression):
        """Add a filter to the query"""

        filter_node = FilterNode.from_expression(filter)
        self._filter_nodes.append(filter_node)

        for ref in filter_node.references:
            self.add_reference(ref)
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
        columns = [ref.as_column(self._registry) for ref in self._references]

        # Establish base query
        query = exp.select(*columns)

        base_table = base_model.table_exp
        base_table_with_alias = base_table.as_(deepest_reference.traverser().alias(base_model.name))
        query = query.from_(base_table_with_alias)

        # Add joins
        joiner = QueryJoiner(query, base_model, self._registry)
        for ref in self._references:
            joiner.join_reference(ref)

        query = joiner.joined_query

        # Add filters
        for filter_node in self._filter_nodes:
            filter_node.resolve(self._registry)

        # Apply appropriate group by
        query = query.group_by(*columns)

        if self._limit:
            query = query.limit(self._limit)

        return query


class QueryJoiner:
    def __init__(self, select: exp.Select, base_model: Model, registry: Registry):
        self._select = select
        self._base_model = base_model
        self._registry = registry
        self._already_joined: set[str] = set()
        self._already_joined.add(base_model.name)

    def join_reference(self, reference: AttributeReference):
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
        print(f"Joining `{from_model_name}` to `{to_model_name}` through `{through_attribute}`")
        registry = self._registry
        query = self._select

        join_path = registry.join_relationships(
            from_model_name, to_model_name, through_attribute=through_attribute
        )
        from_model = registry.get_model(from_model_name)

        print(f"Join path: {join_path}")

        for relationship in join_path:
            referenced_model = registry.get_model(relationship.model_ref)
            referenced_model_alias = create_alias(relationship.model_ref)

            referenced_model_table = referenced_model.table_exp.as_(referenced_model_alias)

            if referenced_model_alias in self._already_joined:
                continue

            if relationship.join_table:
                join_table = exp.to_table(relationship.join_table)
                join_table_alias = create_alias(join_table.name)
                join_table = join_table.as_(join_table_alias)

                query = query.join(
                    join_table,
                    on=f"{from_table_alias}.{from_model.primary_key} = {join_table_alias}.{relationship.self_key_column}",
                    join_type="left",
                )
                query = query.join(
                    referenced_model_table,
                    on=f"{join_table_alias}.{relationship.foreign_key_column} = {referenced_model_alias}.{referenced_model.primary_key}",
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
