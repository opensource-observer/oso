"""Semantic Layer Type Definitions

The semantic layer provides a structured way to access any data model. This is
heavily inspired by prior work with cube.dev, looker, and some new work we've
seen in Snowflake. This semantic layer library is designed to generate SQL
queries as opposed to directly running them. It is powered by sqlglot and
therefore the final sql can render to any dialect supported by sqlglot.

See our documentation for more information at https://docs.opensource.observer.
"""
from __future__ import annotations

import hashlib
import logging
import textwrap
import typing as t
from collections import deque
from enum import Enum
from graphlib import TopologicalSorter

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp, parse_one

from .errors import InvalidAttributeReferenceError
from .utils import exp_to_str, hash_expressions

logger = logging.getLogger(__name__)


def coerce_to_tables_column(ref: str, expected_table: str = "self") -> exp.Expression:
    """Coerces a string reference to a column in a specific table."""
    column = exp.to_column(ref)

    if column.table == expected_table:
        return column
    if column.table == "":
        return exp.to_column(f"{expected_table}.{ref}")

    raise ValueError(f"{ref} is not a valid {expected_table} reference")


class QueryRegistry(t.Protocol):
    def __init__(self, registry: Registry): ...
    def add_reference(self, reference: AttributePath) -> t.Self: ...
    def select(self, *selects: str) -> t.Self: ...
    def where(self, *filters: str) -> t.Self: ...
    def add_limit(self, limit: int) -> t.Self: ...
    def build(self) -> exp.Expression: ...


class RegistryDAG:
    """A DAG of models and views that can be used to generate SQL queries.

    This is used to determine the order in which models and views should be joined.
    """

    adjacency_map: t.Dict[str, t.Set[str]]

    def __init__(self):
        self.adjacency_map = {}

    def add(self, model: "Model"):
        """Inserts the model into the registry and updates the adjacency map."""

        # Register the model under the given name
        self.adjacency_map[model.name] = set()

        # Gets all the names of related models
        reference_names = list(map(lambda x: x.ref_model, model.relationships))

        adj_set = self.adjacency_map.get(model.name, set())
        adj_set = adj_set.union(set(reference_names))
        self.adjacency_map[model.name] = adj_set

    def check_cycle(self):
        """Check if there are any cycles in the directed graph.

        Throws an error if a cycle is detected.
        """
        # 0: unvisited (white), 1: visiting (gray), 2: visited (black)
        color = {node: 0 for node in self.adjacency_map}

        def cycle_dfs(node: str):
            # Mark as visiting (gray)
            color[node] = 1

            # Visit all adjacent nodes
            for neighbor in self.adjacency_map.get(node, set()):
                neighbor_color = color[neighbor]
                if neighbor_color == 1:
                    raise ValueError(f"Cycle detected at model {neighbor}")
                elif neighbor_color == 0:
                    cycle_dfs(neighbor)

            # Mark as visited (black)
            color[node] = 2
            return False

        # Check for cycles starting from each unvisited node
        for node in self.adjacency_map:
            if color[node] == 0:
                cycle_dfs(node)

    def find_best_join_tree(self, references: list[AttributePath]):
        """Finds the join tree with the least amount of nodes (models) for the given references."""
        join_trees = sorted(
            [
                tree
                for tree in (
                    self.build_join_tree(root.base_model, references)
                    for root in references
                )
                if tree is not None
            ],
            key=lambda x: len(x),
        )
        if len(join_trees) == 0:
            raise ModelHasNoJoinPath(
                "No join tree found for the given references. Ensure that the references are valid and that the models are registered."
            )
        return join_trees[0]

    def build_join_tree(self, root: str, references: list[AttributePath]):
        # Build a tree rooted at root
        queue = deque([root])
        parents = {root: root}

        while queue:
            current = queue.popleft()
            for child in self.adjacency_map.get(current, set()):
                if child not in parents:
                    parents[child] = current
                    queue.append(child)

        # Only include in the tree models/paths that are referenced
        filtered_parents = {root: root}
        for reference in references:
            traverser = reference.traverser()
            while True:
                curr_model = traverser.current_model_name
                while curr_model != root and curr_model not in filtered_parents:
                    if curr_model not in parents:
                        return None
                    filtered_parents[curr_model] = parents[curr_model]
                    curr_model = parents[curr_model]
                if not traverser.next():
                    break

        return JoinTree(root, filtered_parents)


class JoinTree:
    root: str
    parents: dict[str, str]

    def __init__(self, root: str, parents: dict[str, str]):
        self.root = root
        self.parents = parents

        self.depths = {}
        self._calculate_depths()

    def __len__(self):
        return len(self.parents)

    def _calculate_depths(self):
        def _get_depth(node: str) -> int:
            if node in self.depths:
                return self.depths[node]
            if node == self.root:
                self.depths[node] = 0
                return 0

            parent = self.parents[node]
            depth = _get_depth(parent) + 1
            self.depths[node] = depth
            return depth

        for node in self.parents:
            _get_depth(node)

    def get_path(self, from_node: str, to_node: str):
        if from_node not in self.parents:
            raise ValueError(f"Node {from_node} not found in join tree")
        if to_node not in self.parents:
            raise ValueError(f"Node {to_node} not found in join tree")
        if from_node == to_node:
            return []

        from_depth = self.depths[from_node]
        to_depth = self.depths[to_node]
        current_from = from_node
        current_to = to_node

        # Bring both nodes to the same depth level
        # Move the deeper node up until both are at the same depth
        from_path = []
        to_path = []

        while from_depth > to_depth:
            from_path.append(current_from)
            current_from = self.parents[current_from]
            from_depth -= 1

        while to_depth > from_depth:
            to_path.append(current_to)
            current_to = self.parents[current_to]
            to_depth -= 1

        # Now both nodes are at the same depth, move both up until they meet (LCA)
        while current_from != current_to:
            from_path.append(current_from)
            to_path.append(current_to)
            current_from = self.parents[current_from]
            current_to = self.parents[current_to]

        lca = current_from

        to_path.reverse()
        result = from_path + [lca] + to_path

        return result


class BoundModelAttribute(t.Protocol):
    def to_query_component(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: "Registry",
    ) -> "QueryComponent":
        """Returns the QueryComponent for the bound query part"""
        ...

    def validate(self): ...


class UnboundModelAttribute(t.Protocol):
    def bind(
        self, model: "Model", dependencies: dict[str, "AttributePath"]
    ) -> "BoundModelAttribute":
        """Binds the query part to the given model and returns a attribute"""
        ...

    def attribute_references(self) -> t.List["AttributePath"]:
        """Returns the references for model attributes"""
        ...


Q = t.TypeVar("Q", bound=QueryRegistry)


class Registry(t.Generic[Q]):
    """A registry for semantic models and views. The generic type Q must follow
    the QueryRegistry protocol. By default this relies on the QueryBuilder class
    available in this library.

    Args:
        query_builder: The QueryRegistry compliant class constructor to use for
        the registry that must follow the QueryRegistry protocol. If not
        provided, defaults to the QueryBuilder class.
    """
    models: t.Dict[str, "Model"]
    dag: RegistryDAG
    views: t.Dict[str, "View"]
    check_cycle: bool = False

    def __init__(self, query_builder: type[Q] | None = None):
        from .query import QueryBuilder

        self.query_builder: type[Q] = query_builder or QueryBuilder  # type: ignore[assignment]
        self.models = {}
        self.views = {}
        self.sorted_model_names = None
        self.dag = RegistryDAG()

    def register(self, model: "Model", repoen: bool = False):
        """Inserts the model into the registry and updates the adjacency map.

        Cycles are not allowed in the registry. If a cycle is detected, an error
        will be raised on later calls
        """

        self.models[model.name] = model
        # Register the model under the given name
        self.dag.add(model)
        self.check_cycle = True

    def register_view(self, view: "View"):
        self.views[view.name] = view

    def get_model(self, name: str) -> "Model":
        return self.models[name]

    def get_view(self, name: str) -> "View":
        return self.views[name]

    def query_from_object(self, semantic_query: "SemanticQuery"):
        """Allows initializing a query builder from a SemanticQuery object."""

        query = self.select(*semantic_query.selects)
        if semantic_query.filters:
            query = query.where(*semantic_query.filters)
        if semantic_query.limit:
            query = query.add_limit(semantic_query.limit)
        return query

    def select(self, *selects: str):
        """Returns a new query builder for the registry"""
        if self.check_cycle:
            self.dag.check_cycle()

        query_builder = self.query_builder(self)
        for select in selects:
            if not isinstance(select, str):
                raise ValueError(f"Select must be a string, got {type(select)}")
        query_builder = query_builder.select(*selects)
        return query_builder

    def describe(self) -> str:
        """Returns a description of the registry used for an LLM prompt"""

        description = "This is the semantic model available to query\n"

        description += "# All Available Models\n"
        for model in self.models.values():
            description += model.describe() + "\n"

        return description
    
    def expand_reference(
        self,
        reference: "AttributePath",
    ) -> t.List["AttributePath"]:
        """Given a reference, walk it and resolve all of the related references"""
        final = reference.final_attribute()

        model = self.get_model(exp_to_str(final.table))
        sub_references = model.get_attribute_references(exp_to_str(final.this))
        if len(sub_references) == 0:
            return [reference]
        else:
            traverser = reference.traverser()
            traverser.to_end()

            expanded_references: t.List[AttributePath] = [reference]

            for sub_reference in sub_references:
                # Rewrite the sub reference to the current model
                expanded_references.extend([
                    traverser.create_scoped_reference(ref) for ref in self.expand_reference(sub_reference)
                ])
            return expanded_references

    def get_attribute_from_reference(self, reference: "AttributePath") -> "BoundDimension | BoundMeasure | BoundRelationship":
        attr = reference.final_attribute()

        model = self.get_model(exp_to_str(attr.table))
        attribute_name = exp_to_str(attr.this)

        return model.get_attribute(
            attribute_name
        )



class GenericExpression(BaseModel):
    """Specifically not the sqlglot expression type, but a generic internal type
    for expressions

    When defining a model the queries that make up a model all inherit from this
    base class. Additionally, all expressions within a query (selects and
    filters) also inherit from this class.

    There are two main types of expressions:

    1. RawExpression: This is a raw SQL expression. Any references to columns is
       considered should specifically be references to the _actual_ column names
       on the underlying table.
    2. SemanticExpression: This is a semantic expression that is in the semantic
       context and can reference models and attributes. When used in a dimension
       or measure it may only reference `self`. In queries, it may reference any
       model attribute available in the registry.

    In both cases, the query string is processed at the time of instantiation
    and all references to columns or other semantic layer attributes are
    converted to sqlglot exp.Anonymous (which represent some unknown sql
    function if rendered to sql). This is done to allow for us to preprocess all
    of the available references in an expression and replace them with the
    correct table.column reference in the final query that is generated. For
    RawExpression, the anonymous function is `$column_ref`. For
    SemanticExpression, the anonymous function is `$semantic_ref`.

    To get the final SQL expression for a given GenericExpression, you must call
    the `resolve` method. This will convert all of the exp.Anonymous expressions
    that match the `$semantic_ref` and `$column_ref` into the correct
    table.column references for a given sql query.
    """

    query: str

    @model_validator(mode="after")
    def validate_query(self):
        """Validates that the query is a valid SQL expression"""
        try:
            self._expression = self.to_sqlglot_expression()
        except Exception as e:
            raise ValueError(f"Invalid SQL expression: {e}")

        return self

    @property
    def expression(self) -> exp.Expression:
        return self._expression

    def to_sqlglot_expression(self) -> exp.Expression:
        """Returns the SQL expression for the generic expression"""
        raise NotImplementedError(
            "This method should be implemented by subclasses to return the SQL expression for the generic expression"
        )

    def columns(self) -> t.List[exp.Column]:
        """Returns the columns in the expression. By default a generic
        expressions are _not_ allowed to reference columns"""
        raise ValueError(
            "GenericExpression columns method does not allow self references by default. Use allow_self=True to allow self references."
        )

    def references(self, allow_self: bool = False) -> t.List["AttributePath"]:
        """Returns the semantic references in the expression

        Args:
            allow_self: If True, allows references to the `self` model. Defaults to False.

        Returns:
            A list of AttributePath objects representing the semantic references in the expression.
        """

        raise NotImplementedError(
            "This method should be implemented by subclasses to return the semantic references in the expression"
        )

    def placeholder_expression_to_attribute_path(
        self, node: exp.Anonymous
    ) -> "AttributePath":
        """Converts a placeholder expression to an AttributePath.

        This is used to convert the $semantic_ref and $column_ref expressions
        into AttributePath objects.
        """
        if not node.expressions:
            raise ValueError("Placeholder expression must have at least one expression")
        reference_literal = exp_to_str(node.expressions[0])
        try:
            return AttributePath.from_string(reference_literal)
        except InvalidAttributeReferenceError as e:
            raise ValueError(f"Invalid semantic reference: {e}")

    def resolve(
        self,
        registry: Registry,
        self_model_name: str = "",
        traverser: AttributePathTraverser | None = None,
    ) -> exp.Expression:
        """Returns the SQL expression for an expression. This generic resolve
        method turns $semantic_ref, and $column_ref anonymous expressions into
        executable sql based on the current registry and traverser.

        Args:
            registry: The registry
            self_model_name: The name of the model that this expression is being
                resolved for. This is used to determine the current model in the
                traverser and should generally only be set by a BoundDimension,
                BoundMeasure, or BoundRelationship.
            traverser: The traverser to use for resolving the expression. If not
                provided, a new traverser will be created from the root.
        
        Returns:
            The resolved SQL expression as a sqlglot Expression object.
        """
        if not traverser:
            traverser = AttributePathTraverser.from_root()

        def convert_column(node: exp.Expression):
            if isinstance(node, exp.Anonymous):
                anonymous_function_name = exp_to_str(node.this)
                if anonymous_function_name not in ["$semantic_ref", "$column_ref"]:
                    # If this is not a semantic reference or column reference, we can skip it
                    return node

                # Get the model reference from the anonymous expression
                reference = self.placeholder_expression_to_attribute_path(node)
                reference = traverser.create_scoped_reference(reference)

                column_traverser = reference.traverser()
                column_traverser.to_end()
                current_model_name = column_traverser.current_model_name
                if current_model_name == "self":
                    # If the current model is self, we need to use the self_model_name
                    current_model_name = self_model_name
                model = registry.get_model(current_model_name)

                if anonymous_function_name == "$semantic_ref":
                    # If this is a semantic reference then we need to recursively resolve it
                    attribute = model.get_attribute(
                        column_traverser.current_attribute_name
                    )
                    match attribute:
                        case BoundDimension():
                            resolved = attribute.resolve(
                                registry=registry,
                                traverser=column_traverser,
                            )
                            return resolved
                        case BoundMeasure():
                            resolved = attribute.resolve(
                                registry=registry,
                                traverser=column_traverser,
                            )
                            return resolved
                        case BoundRelationship():
                            raise ValueError(
                                f"Semantic reference {reference} cannot resolve to a relationship at this time. Only dimensions and measures are allowed."
                            )

                elif anonymous_function_name == "$column_ref":
                    # If this is a column reference then we need to simply resolve to the model's column
                    col = exp.to_column(
                        f"{column_traverser.alias(current_model_name)}.{column_traverser.current_attribute_name}",
                    )
                    return col
            return node

        return self._expression.transform(convert_column)
    
    @classmethod
    def is_ref_node(cls, node: exp.Expression) -> bool:
        """Checks if the node is an anonymous reference node.

        This is used to determine if the node is a semantic reference or a column
        reference.
        """
        return isinstance(node, exp.Anonymous) and (
            exp_to_str(node.this) == "$semantic_ref"
            or exp_to_str(node.this) == "$column_ref"
        )
    
    @classmethod
    def is_column_ref_node(cls, node: exp.Expression) -> bool:
        """Checks if the node is a column reference node.

        This is used to determine if the node is a column reference.
        """
        return isinstance(node, exp.Anonymous) and exp_to_str(node.this) == "$column_ref"
    
    @classmethod
    def is_semantic_ref_node(cls, node: exp.Expression) -> bool:
        """Checks if the node is a semantic reference node.

        This is used to determine if the node is a semantic reference.
        """
        return isinstance(node, exp.Anonymous) and exp_to_str(node.this) == "$semantic_ref"

class SemanticExpression(GenericExpression):
    """A string expression that is in the semantic context"""

    def to_sqlglot_expression(self) -> exp.Expression:
        """Transforms the query into a sqlglot expression"""

        def transform(node: exp.Expression) -> exp.Expression:
            if is_expression_attribute_reference(node):
                # For anything that's an attribut path we need to resolve it
                if isinstance(node, exp.Column):
                    # if it's a column this is a simple resolution simply to the column via the registry
                    logger.debug(f"Found column reference: {node}")
                    model_name = exp_to_str(node.table)
                    column_name = exp_to_str(node.this)
                    reference = AttributePath.from_string(f"{model_name}.{column_name}")
                else:
                    logger.debug(f"Found non column reference: {node}")
                    # Check for self in reference path
                    reference_path = node.sql(dialect="duckdb").split("->")
                    for i in range(len(reference_path)):
                        ref = reference_path[i]
                        as_column = exp.to_column(ref)
                        model_name = exp_to_str(as_column.table)

                        if model_name == "self":
                            reference_path[i] = (
                                f"{model_name}.{exp_to_str(as_column.this)}"
                            )
                    reference = AttributePath(path=reference_path)

                refs_as_literals = exp.Literal.string(str(reference))

                return exp.Anonymous(
                    this="$semantic_ref", expressions=[refs_as_literals]
                )
            return node

        return parse_one(self.query).transform(transform)

    def references(self, allow_self: bool = False) -> t.List["AttributePath"]:
        """Returns the semantic references in the expression"""
        glot_expression = self._expression
        all_reference_placeholders = glot_expression.find_all(exp.Anonymous)
        references: t.List[AttributePath] = []
        for reference_placeholder in all_reference_placeholders:
            if reference_placeholder.this == "$semantic_ref":
                # This is a semantic reference, we need to parse it
                if not reference_placeholder.expressions:
                    raise ValueError(
                        "Semantic reference must have at least one expression"
                    )
                reference_literal = exp_to_str(reference_placeholder.expressions[0])
                try:
                    reference = AttributePath.from_string(reference_literal)
                except InvalidAttributeReferenceError as e:
                    raise ValueError(f"Invalid semantic reference: {e}")
                if not allow_self and reference.is_self_reference():
                    raise ValueError(
                        f"SemanticExpression {self.query} not allowed to reference `self` model. Only valid in Dimension, Measure, and Relationship definitions."
                    )
                references.append(reference)
        return references


class RawExpression(GenericExpression):
    """A raw SQL expression that is not in the semantic context.

    This is used to pass raw SQL expressions to the semantic layer without
    parsing them. However, the special table `self` is used to refer to the
    current model's table.
    """

    query: str

    @model_validator(mode="after")
    def validate_only_self_references(self):
        """Validates that the expression only references `self`

        RawExpressions have no access to the semantic layer and therefore
        cannot reference other models. They can only reference the current model's
        table.
        """
        for column in self.columns():
            if exp_to_str(column.table) != "self":
                raise ValueError(
                    f"Raw expression {self.query} cannot reference another model. Found reference to {column.table}. Only use `self`"
                )
        return self

    def to_sqlglot_expression(self) -> exp.Expression:
        def convert_column(node: exp.Expression):
            if isinstance(node, exp.Column):
                return exp.Anonymous(
                    this="$column_ref",
                    expressions=[exp.Literal.string(f"{node.table}.{node.this}")],
                )
            return node

        return parse_one(self.query).transform(convert_column)

    def columns(self) -> t.List[exp.Column]:
        """Returns the columns in the expression"""
        expression = parse_one(self.query)
        return list(expression.find_all(exp.Column))

    def references(self, allow_self: bool = False) -> t.List["AttributePath"]:
        return []


def raw_exp(query: str) -> RawExpression:
    """Creates a raw expression from a string"""
    return RawExpression(query=query)


def semantic_exp(query: str) -> SemanticExpression:
    """Creates a semantic expression from a string"""
    return SemanticExpression(query=query)


class MeasureOperationType(str, Enum):
    """The type of operation to perform on the measure.

    This is used to determine how to aggregate the measure.
    """

    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    MAX = "max"
    MIN = "min"
    FIRST = "first"
    LAST = "last"
    PERCENTILE = "percentile"
    PERCENTILE_CONT = "percentile_cont"
    PERCENTILE_DISC = "percentile_disc"


class Measure(BaseModel):
    name: str
    description: str = ""
    query: RawExpression | SemanticExpression | str = ""

    @model_validator(mode="after")
    def process_metric(self):
        if isinstance(self.query, str):
            expression = SemanticExpression(query=self.query)
        else:
            expression = self.query

        self._expression = expression

        return self

    @property
    def columns(self) -> t.List[exp.Column]:
        """Returns the columns in the expression"""
        if isinstance(self._expression, RawExpression):
            return list(self._expression.columns())
        else:
            return []

    def bind(self, model: "Model") -> "BoundMeasure":
        """Returns the bound metric for the given model"""

        return BoundMeasure(
            model=model,
            measure=self,
        )

    def resolve(
        self,
        self_model_name: str,
        registry: Registry,
        traverser: "AttributePathTraverser | None" = None,
    ) -> exp.Expression:
        """Returns a resolved SQL expression for the measure."""

        return self._expression.resolve(
            traverser=traverser,
            self_model_name=self_model_name,
            registry=registry,
        )

    def references(self, allow_self: bool = False) -> t.List["AttributePath"]:
        """Returns the semantic references in the measure expression"""
        return self._expression.references(allow_self=allow_self)


class BoundMeasure:
    model: "Model"
    measure: Measure

    def __init__(self, model: "Model", measure: Measure):
        self.model = model
        self.measure = measure

    def resolve(
        self,
        registry: Registry,
        traverser: "AttributePathTraverser | None" = None,
    ) -> exp.Expression:
        """Returns the QueryComponent for the measure"""

        return self.measure.resolve(
            traverser=traverser,
            self_model_name=self.model.name,
            registry=registry,
        )

    def references(self) -> t.List["AttributePath"]:
        """Returns the semantic references in the dimension expression"""
        return [
            ref.rewrite_self(self.model.name)
            for ref in self.measure.references(allow_self=True)
        ]

class Select(BaseModel):
    """Represents the select part of a query. This should just be a semantic reference"""

    query: SemanticExpression | str = Field(
        description="A semantic expression for the select part of the query"
    )

    @model_validator(mode="after")
    def process_select(self):
        if isinstance(self.query, str):
            expression = SemanticExpression(query=self.query)
        else:
            expression = self.query

        references = expression.references(allow_self=False)

        # We currently don't support adding constants as a select expression
        if len(references) != 1:
            raise ValueError(
                f"Select expression must be a single semantic reference, got {len(references)} references: {references}"
            )

        # Ensure that the sqlglot expression is only a single reference or a single
        # reference and an alias
        sqlglot_expr = expression.to_sqlglot_expression()
        if not GenericExpression.is_semantic_ref_node(sqlglot_expr):
            if not isinstance(sqlglot_expr, exp.Alias):
                raise ValueError(
                    f"Select expression must be a semantic reference or a semantic reference with an alias, got {type(sqlglot_expr)}"
                )

        self._expression = expression

        return self

    @property
    def expression(self) -> SemanticExpression:
        """Returns the semantic expression for the select part of the query"""
        return self._expression
    
    def resolve(self, registry: Registry, traverser: AttributePathTraverser | None = None) -> exp.Expression:
        """Returns a resolved SQL expression for the select part of the query."""

        return self._expression.resolve(
            traverser=traverser,
            self_model_name="",
            registry=registry,
        )

    def references(self) -> t.List["AttributePath"]:
        """Returns the semantic references in the select expression"""
        return self._expression.references(allow_self=False)

    def is_aggregate(self, registry: Registry) -> bool:
        """Returns whether the select expression is an aggregate function."""
        # If this references a measure, then it is an aggregate function
        references = self.references()
        for reference in references:
            attribute = registry.get_attribute_from_reference(reference)
            if isinstance(attribute, BoundMeasure):
                return True
        return False

    def alias(self):
        """Returns the alias for the select expression"""
        # The alias is the last part of the reference path
        # Check the expression if it explicitly has an alias
        sqlglot_expr = self._expression.to_sqlglot_expression()
        if isinstance(sqlglot_expr, exp.Alias):
            # If the expression is an alias, we use that as the alias

            return exp_to_str(sqlglot_expr.alias)
        else:
            reference = self.references()[0]
            return reference.to_select_alias()

    
    
class Filter(BaseModel):
    """Represents the filter part of a query. This should can be any semantic
    expression or raw expression that resolves to a boolean expression."""

    query: SemanticExpression | str = Field(
        description="A semantic expression for the filter"
    )

    @model_validator(mode="after")
    def process_filter(self):
        if isinstance(self.query, str):
            expression = SemanticExpression(query=self.query)
        else:
            expression = self.query

        self._expression = expression

        return self
    
    @property
    def expression(self) -> SemanticExpression:
        """Returns the semantic expression for the filter"""
        return self._expression

    def resolve(
        self,
        registry: Registry,
        traverser: AttributePathTraverser | None = None,
    ) -> exp.Expression:
        """Returns a resolved SQL expression for the dimension."""

        return self._expression.resolve(
            traverser=traverser,
            self_model_name="",
            registry=registry,
        )

    def references(self) -> t.List["AttributePath"]:
        """Returns the semantic references in the dimension expression"""
        return self._expression.references(allow_self=False)
    
    def is_aggregate(self, registry: Registry) -> bool:
        """Returns whether the filter expression is an aggregate function."""
        # If this references a measure, then it is an aggregate function (this likely needs to be fixed but)
        references = self.references()
        for reference in references:
            attribute = registry.get_attribute_from_reference(reference)
            if isinstance(attribute, BoundMeasure):
                return True
        return False

    def alias(self) -> str:
        return ""


class Dimension(BaseModel):
    """A dimension is a column or expression that must resolve to a column in
    the table.

    The dimension can either be a simple column reference or a non-aggregating
    expression.
    """

    name: str
    description: str = ""
    query: RawExpression | SemanticExpression | str = Field(
        default="",
        description=textwrap.dedent(
            """
        A SQL expression for the dimension. If using a "RawExpression", it any
        columns in the query are listed as expected columns in the table. If
        using a SemanticExpression, it must resolve to a different dimension in
        the model. It may _not_ resolve to a measure or relationship. If this is
        not provided, the dimension will default to the column with the same
        name as the dimension.

        Examples:
        
            Let's assume we initialize a model with an attribute `time` that has
            the raw expression `RawExpression(query='self.time')`. Let's also
            assume this is stored as a unix timestamp. If we wanted to have
            another attribute `date` we could reference the time column OR the
            time semantic attribute using the same string with these two
            expressions:

                RawExpression(query="CAST(from_unixtime(self.time) AS DATE)")
                SemanticExpression(
                    query="CAST(from_unixtime(self.time) AS DATE)"
                )

            If we then wanted to create an attribute `month` it is likely
            easiest to use the semantic expression, but also possible to do this
            as a RawExpression. Here's how you'd do it in both cases:

                RawExpression(
                    query="timestamp_trunc('month',from_unixtime(self.time))"
                )
                SemanticExpression(query="timestamp_trunc('month', self.date)")
    """
        ),
    )
    column_name: str = Field(
        default="",
        description=textwrap.dedent(
            """
        The name of the column on the table, this _must_ be a column on the
        actual underlying table in the database. This is automatically converted
        into a RawExpression.
    """
        ),
    )

    @model_validator(mode="after")
    def process_dimension(self):
        if self.query and self.column_name:
            raise ValueError("Cannot specify both query and column_name for dimension")
        if not self.query and not self.column_name:
            self.column_name = self.name

        if self.query:
            if isinstance(self.query, str):
                # If the query is a string, we assume it's a semantic expression
                self.query = SemanticExpression(query=self.query)
            expression = self.query
        else:
            expression = RawExpression(
                query=exp.Column(
                    table=exp.to_identifier("self"),
                    this=exp.to_identifier(self.column_name),
                ).sql(dialect="duckdb")
            )

        match expression:
            case RawExpression():
                # check the columns in the expression and ensure they only reference `self`
                references: t.List[AttributePath] = []
                columns = list(expression.columns())
                for column in columns:
                    if column.table != "self":
                        raise ValueError(
                            f"Dimension {self.name} cannot reference another model. Found reference to {column.table}. Only use `self`"
                        )
            case SemanticExpression():
                # Ensure all references point to self
                columns = []
                references = expression.references(allow_self=True)
                for reference in references:
                    if not reference.is_self_reference():
                        raise ValueError(
                            f"Dimension {self.name} cannot reference another model. Found reference to {reference}. Only use `self`"
                        )
        self._columns = columns
        self._expression = expression

        return self

    @property
    def columns(self) -> t.List[exp.Column]:
        """Returns the actual columns that this dimension defines. The Model
        class collects these in order to determine the minimal compatible schema
        for that the underlying table must implement."""

        return list(self._columns)

    def bind(self, model: "Model") -> "BoundDimension":
        return BoundDimension(
            model=model,
            dimension=self,
        )

    def resolve(
        self,
        self_model_name: str,
        registry: Registry,
        traverser: AttributePathTraverser | None = None,
    ) -> exp.Expression:
        """Returns a resolved SQL expression for the dimension."""

        return self._expression.resolve(
            traverser=traverser,
            self_model_name=self_model_name,
            registry=registry,
        )

    def references(self, allow_self: bool = False) -> t.List["AttributePath"]:
        """Returns the semantic references in the dimension expression"""
        if isinstance(self._expression, SemanticExpression):
            return self._expression.references(allow_self=allow_self)
        else:
            return []


class BoundDimension:
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: "Model"
    dimension: Dimension

    def __init__(self, model: "Model", dimension: Dimension):
        self.model = model
        self.dimension = dimension

    def resolve(
        self,
        registry: Registry,
        traverser: "AttributePathTraverser | None" = None,
    ) -> exp.Expression:
        """Returns the QueryComponent"""

        return self.dimension.resolve(
            traverser=traverser,
            self_model_name=self.model.name,
            registry=registry,
        )

    def references(self) -> t.List["AttributePath"]:
        """Returns the semantic references in the dimension expression"""
        return [
            ref.rewrite_self(self.model.name) for ref in self.dimension.references()
        ]


class RelationshipType(str, Enum):
    """The type of reference to use for the model.

    This is used to determine how to join the models together.
    """

    ONE_TO_ONE = "one_to_one"
    MANY_TO_ONE = "many_to_one"
    ONE_TO_MANY = "one_to_many"


class Relationship(BaseModel):
    """Defines a relationship between two models in the semantic layer.

    A Relationship represents how one model connects to another model through
    foreign key references. This enables the semantic layer to understand
    data relationships and generate appropriate JOIN clauses in SQL queries.

    Attributes:
        name: Optional name for the relationship. If not provided, defaults to ref_model.
        description: Optional human-readable description of the relationship.
        type: The type of relationship (ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE).
        source_foreign_key: Column(s) in the source (current) model that reference the target model.
                           Can be a single column name or list of column names for composite keys.
        ref_model: Name of the target model being referenced.
        ref_key: Column(s) in the target model that is referenced.
                        Can be a single column name or list of column names for composite keys.
    """

    name: str = ""
    description: str = ""
    type: RelationshipType
    source_foreign_key: str | list[str]
    ref_model: str
    ref_key: str | list[str]

    @model_validator(mode="after")
    def process_relationship(self):
        if not self.name:
            # If no name is provided, use the model_ref as the name
            self.name = self.ref_model

        if isinstance(self.source_foreign_key, str):
            self.source_foreign_key = [self.source_foreign_key]
        if isinstance(self.ref_key, str):
            self.ref_key = [self.ref_key]

        assert len(self.source_foreign_key) == len(
            self.ref_key
        ), f"Source foreign key {self.source_foreign_key} and reference foreign key {self.ref_key} must have the same length"

        return self

    def bind(self, model: "Model") -> "BoundRelationship":
        """Binds the relationship to a model and returns a BoundRelationship"""

        return BoundRelationship(
            model=model,
            name=self.name,
            type=self.type,
            source_foreign_key=(
                self.source_foreign_key
                if isinstance(self.source_foreign_key, list)
                else [self.source_foreign_key]
            ),
            ref_model=self.ref_model,
            ref_foreign_key=(
                self.ref_key if isinstance(self.ref_key, list) else [self.ref_key]
            ),
        )


class BoundRelationship:
    model: "Model"
    name: str = ""
    type: RelationshipType
    source_foreign_key: list[str]
    ref_model: str
    ref_key: list[str]

    def __init__(
        self,
        *,
        model: "Model",
        name: str,
        type: RelationshipType,
        source_foreign_key: list[str],
        ref_model: str,
        ref_foreign_key: list[str],
    ):
        self.model = model
        self.name = name
        self.type = type
        self.source_foreign_key = source_foreign_key
        self.ref_model = ref_model
        self.ref_key = ref_foreign_key


class ViewConnector(BaseModel):
    def primary_key(self, model_name) -> t.Optional[str | exp.Expression]:
        return None

    def time_column(self, model_name) -> t.Optional[str]:
        return None

    def dimensions(self, model_name) -> t.List[Dimension]:
        return []

    def measures(self, model_name) -> t.List[Measure]:
        return []


class View(BaseModel):
    """A generic set of dimensions and measures that can be queried together."""

    name: str
    description: str = ""
    connector: ViewConnector


class Model(BaseModel):
    """A model is a semantic layer representation of a table in the warehouse as
    a set of dimensions, measures, and relationships."""

    name: str
    description: str = ""
    table: str

    primary_key: str | t.List[str] = ""
    time_column: t.Optional[str] = None

    # These are additional interfaces to the model
    views: t.List[View | str] = Field(default_factory=lambda: [])

    dimensions: t.List[Dimension] = Field(default_factory=lambda: [])
    measures: t.List[Measure] = Field(default_factory=lambda: [])
    relationships: t.List[Relationship] = Field(default_factory=lambda: [])

    @model_validator(mode="after")
    def build_attribute_lookup(self):
        """Builds a lookup of the references in the model"""
        attributes: dict[str, BoundDimension | BoundMeasure | BoundRelationship] = {}
        known_columns: t.Set[str] = set()

        # Topologically sort all of the dimensions, measures, and relationships in the model
        attribute_graph: t.Dict[str, t.Set[str]] = {}
        attribute_references: t.Dict[str, t.List[AttributePath]] = {}

        for dimension in self.dimensions:
            if dimension.name in attribute_graph:
                raise ValueError(
                    f"Dimension {dimension.name} already exists in model {self.name}"
                )
            references = [ref.rewrite_self(self.name) for ref in dimension.references(allow_self=True)]

            known_columns.update(
                set([
                    exp_to_str(col.this) 
                    for col in dimension.columns
                ]),
            )
            attribute_graph[dimension.name] = set()
            attribute_references[dimension.name] = references

            for reference in references:
                if reference.is_relationship() or reference.base_model != self.name:
                    raise ValueError("Cannot reference a relationship in a dimension")
                # Attribute/Column name
                attribute_name = exp_to_str(reference.final_attribute().this)

                if attribute_name == dimension.name:
                    # If the attribute name is the same as the dimension name, we can skip it.
                    # For a dimension this just means that the dimension is a column in the table
                    continue

                attribute_graph[dimension.name].add(
                    exp_to_str(reference.final_attribute().this)
                )

            attributes[dimension.name] = dimension.bind(self)

        # Check for cycles in the dimensions
        dimensions_sorter = TopologicalSorter(attribute_graph)
        dimensions_sorter.prepare()

        # Check for cycles in the measures and dimensions
        # For now this only checks for cycles in the current model.
        for measure in self.measures:
            # Ensure we don't have duplicate names
            if measure.name in attributes or measure.name in attribute_graph:
                raise ValueError(
                    f"Measure {measure.name} already exists in model {self.name}"
                )
            references = [ref.rewrite_self(self.name) for ref in measure.references(allow_self=True)]
            attribute_graph[measure.name] = set()
            attribute_references[measure.name] = references

            known_columns.update(
                set([
                    exp_to_str(col.this)
                    for col in measure.columns
                ]),
            )

            for reference in references:
                reference = reference.rewrite_self(self.name)
                if reference.is_relationship() or reference.base_model != self.name:
                    # Relationships are allowed in measures and must be validated at the
                    # registry level
                    continue
                attribute_graph[measure.name].add(
                    exp_to_str(reference.final_attribute().this)
                )

            attributes[measure.name] = measure.bind(self)

        # Ensure we have no cycles in the attribute graph
        attribute_sorter = TopologicalSorter(attribute_graph)
        attribute_sorter.prepare()

        self._model_ref_lookup_by_model_name: dict[str, list[Relationship]] = {}
        for reference in self.relationships:
            if reference.name in attributes:
                raise ValueError(
                    f"{reference.name} already exists in model {self.name}. Must be unique"
                )

            attributes[reference.name] = reference.bind(self)

            if isinstance(reference.source_foreign_key, str):
                known_columns.add(reference.source_foreign_key)
            else:
                known_columns.update(reference.source_foreign_key)

            if reference.ref_model not in self._model_ref_lookup_by_model_name:
                self._model_ref_lookup_by_model_name[reference.ref_model] = []
            self._model_ref_lookup_by_model_name[reference.ref_model].append(reference)

        self._all_attributes = attributes

        if isinstance(self.primary_key, str):
            self._primary_key_expression = coerce_to_tables_column(self.primary_key)
        elif isinstance(self.primary_key, list):
            self._primary_key_expression = hash_expressions(
                *[coerce_to_tables_column(pk) for pk in self.primary_key]
            )

        self._known_columns = known_columns
        self._attribute_references = attribute_references
        return self

    @property
    def known_columns(self) -> t.Set[str]:
        """Returns the known columns in the model

        This is useful for validating that the model is valid for a given sql
        connection. This set of columns should comprise the schema of the table.
        It isn't required to be exhaustive, but at a minimum the connection
        should have the same columns as the known columns.
        """
        return self._known_columns

    def primary_key_expression(self, table_alias: str) -> exp.Expression:
        """Returns the primary key expression for the model given the table alias."""

        def transform_columns(node: exp.Expression):
            if isinstance(node, exp.Column):
                node_table = exp_to_str(node.table)
                if node_table != "self":
                    # Do a check here but this is pretty fatal and should have
                    # been caught at validation time
                    raise ValueError(
                        f"Primary key column {node_table}.{node.this} must be a self reference"
                    )
                return exp.Column(
                    table=exp.to_identifier(table_alias),
                    this=node.this,
                )
            return node

        primary_key_expression = self._primary_key_expression.transform(
            transform_columns
        )
        return primary_key_expression

    @property
    def attribute_names(self) -> t.List[str]:
        """Returns the names of all attributes in the model"""
        return list(self._all_attributes.keys())

    def get_dimension(self, name: str) -> BoundDimension:
        """Returns the dimension with the given name"""
        dimension = self.get_attribute(name)
        if not isinstance(dimension, BoundDimension):
            raise ValueError(f"{name} is not a dimension in model {self.name}")
        return dimension

    def get_relationship(self, name: str) -> BoundRelationship:
        """Returns the relationship with the given name"""
        relationship = self.get_attribute(name)
        if not isinstance(relationship, BoundRelationship):
            raise ValueError(f"{name} is not a relationship in model {self.name}")
        return relationship

    def find_relationship(
        self, *, model_ref: str, name: str = ""
    ) -> "BoundRelationship":
        """Returns the reference with the given name or model_ref"""
        if name == "" and model_ref == "":
            raise ValueError("Must provide either name or model_ref to get reference")

        if name:
            for reference in self.relationships:
                if reference.name == name:
                    if reference.ref_model != model_ref:
                        raise ValueError(
                            f"Reference {name} does not match model_ref {model_ref}"
                        )
                    return self.get_relationship(name)

        for reference in self.relationships:
            references = self._model_ref_lookup_by_model_name[reference.ref_model]
            if len(references) > 1:
                raise ModelHasAmbiguousJoinPath(
                    f"Reference {model_ref} is ambiguous in model {self.name}"
                )
            if reference.ref_model == model_ref:
                relationship = self._all_attributes[reference.name]
                if not isinstance(relationship, BoundRelationship):
                    raise ValueError(
                        f"{reference.name} is not a reference in model {self.name}"
                    )
                return relationship
        raise ValueError(f"Reference {model_ref} not found in model {self.name}")

    @property
    def table_exp(self):
        """Returns the table for the model"""
        return exp.to_table(self.table)

    def get_attribute(
        self, name: str
    ) -> BoundDimension | BoundMeasure | BoundRelationship:
        """Resolves the attribute to a column in the model"""
        if name not in self._all_attributes:
            raise ValueError(f"Attribute {name} not found in model {self.name}")
        return self._all_attributes[name]

    def attributes(self):
        """Returns all attributes in the model"""
        return self._all_attributes.values()

    def describe(self):
        """Returns a description of the model used for an LLM prompt"""

        description = f"## Model: {self.name}\n\n"
        description += f"{self.description}\n"
        description += "\n### Dimensions:\n"
        for dimension in self.dimensions:
            description += (
                f"- `{self.name}.{dimension.name}`: {dimension.description}\n"
            )

        description += "\n### Measures:\n"
        for measure in self.measures:
            description += f"- `{self.name}.{measure.name}`: {measure.description}\n"

        description += "\n### Relationships:\n"
        for relationship in self.relationships:
            description += (
                f"- `{self.name}.{relationship.name}`: "
                f"{relationship.description}. This is a {relationship.type.value} relationship\n"
            )
        ambiguous_rels_descriptions = ""
        include_ambiguous = False
        for (
            model_ref,
            model_relationships,
        ) in self._model_ref_lookup_by_model_name.items():
            if len(model_relationships) > 1:
                include_ambiguous = True
                ambiguous_rels_descriptions += (
                    f"- `{model_ref}`:"
                    f" Any relationships to this model or anything derived from it"
                    f" must use the `->` through syntax to prevent ambiguous joins in the query\n"
                )
        if include_ambiguous:
            description += "\n### Ambiguous Relationships:\n"
            description += ambiguous_rels_descriptions
        description += "\n"
        return description

    def get_attribute_references(
        self, name: str
    ) -> t.List[AttributePath]:
        """Returns the attribute references for the given attribute name"""
        if name not in self._attribute_references:
            raise ValueError(f"Attribute {name} not found in model {self.name}")
        return self._attribute_references[name]


class RollingWindow(BaseModel):
    window: int
    unit: str


class ModelHasNoJoinPath(Exception):
    pass


class ModelHasAmbiguousJoinPath(Exception):
    pass


class Join(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    table: str
    via: str | None = None


class AttributePath(BaseModel):
    path: list[str]

    @model_validator(mode="after")
    def process_ref(self):
        self._columns = [exp.to_column(r.strip()) for r in self.path]

        # Write out normalized path
        self.path = [
            f"{exp_to_str(column.table)}.{exp_to_str(column.this)}"
            for column in self._columns
        ]
        return self

    @classmethod
    def from_string(cls, path: str) -> "AttributePath":
        return cls(path=path.split("->"))

    def traverser(
        self,
        initial_value: str = "",
        parent_traverser: "AttributePathTraverser | None" = None,
    ):
        return AttributePathTraverser.from_reference(
            self,
            initial_value=initial_value,
            parent_traverser=parent_traverser,
        )

    @property
    def base_model(self):
        return self._columns[0].table

    @property
    def columns(self):
        return self._columns

    def is_valid_for_registry(self, registry: Registry):
        """Checks if the reference is valid for the given registry"""
        return self.traverser().is_valid_for_registry(registry)

    def __str__(self) -> str:
        """Returns the string representation of the reference"""
        columns_as_strs = [
            f"{exp_to_str(column.table)}.{exp_to_str(column.this)}"
            for column in self._columns
        ]
        return "->".join(columns_as_strs)

    def to_select_alias(self) -> str:
        """Returns the string representation of the reference as a select alias"""
        columns_as_strs = [
            f"{exp_to_str(column.table)}_{exp_to_str(column.this)}"
            for column in self._columns
        ]
        return "__".join(columns_as_strs)

    def __eq__(self, other: object) -> bool:
        """Checks if the reference is equal to another reference"""
        if not isinstance(other, AttributePath):
            return False
        return self.path == other.path

    def final_attribute(self) -> exp.Column:
        """Returns the final column in the reference"""
        return self._columns[-1]

    def is_relationship(self) -> bool:
        """Checks if the reference is a relationship"""
        return len(self._columns) > 1

    def is_self_reference(self) -> bool:
        """Checks if the reference is a self reference"""
        has_self = False
        for column in self._columns:
            if exp_to_str(column.table) == "self":
                has_self = True
        return has_self

    def rewrite_self(self, self_model_name: str) -> "AttributePath":
        """Rewrites the self reference to the given model name"""
        new_path: list[str] = []
        for column in self._columns:
            if exp_to_str(column.table) == "self":
                new_path.append(f"{self_model_name}.{exp_to_str(column.this)}")
            else:
                new_path.append(f"{exp_to_str(column.table)}.{exp_to_str(column.this)}")
        return AttributePath(path=new_path)


class AttributeTransformerResult(BaseModel):
    """Internal result only used for the attribute reference transformer"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    node: exp.Expression
    references: list[AttributePath]


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


class QueryComponent(t.Protocol):
    """The most basic representation of a part of a query.

    This is used to represent dimensions, measures, and filters in a query.

    Each of those parts of a query should have the following properties:

    * An expression that can be used to generate the SQL
    * 1 or more references related to the expression. We need to know all of
      these to understand how to generate the right joins
    * If the expression is an aggregate function, we need to know if it is
        additive or not. This is used to determine if we need to use ctes or
        not. If the expression is not an aggregate function, we can group by
        this expression.

    The `original` field is used to store the original attribute path or
    SemanticExpression that was used to create this query component.

    The `expression` field is a sqlglot expression that has not been fully
    resolved for the current query. Resolving replaces any column references or
    semantic attributes to the actual columns in the query.
    """

    def is_aggregate(self, registry: "Registry") -> bool:
        """Returns whether the query component is an aggregate function."""
        ...

    def resolve(self, registry: "Registry", traverser: "AttributePathTraverser | None" = None) -> exp.Expression:
        """Returns a resolved SQL expression for the query component.

        This should resolve any references to the actual columns in the query.
        """
        ...

    def references(self) -> t.List[AttributePath]:
        """Returns the semantic references in the query component."""
        ...

    def alias(self) -> str:
        """Returns the alias for the query component. If the component cannot be
        aliased, this should return an empty string.

        This is used to generate the SQL alias for the query component.
        """
        ...


class AttributePathTraverser:
    """AttributeReferences are used to reference a dimension or metric in a
    model.

    Because some models may reference another model more than once. The way this
    would be distinguished would be through different model relationship
    attributes. Path traversal, tracks the joins through these attributes.

    The following table shows how a traverser works, given a path
    `a.b->c.d->e.f`:

    | Index             | 0      | 1               | 2                        |
    |-------------------|--------|-----------------|--------------------------|
    | Through Column    |        | a.b             | c.d                      |
    | Alias for table g | md5(g) | md5(md5(a.b)+g) | md5(md5(md5(a.b)+c.d)+g) |

    This allows us to ensure that we don't duplicate joins by ensuring that each
    level through a given column reference uses the same table alias.
    """

    @classmethod
    def from_root(cls, initial_value: str = ""):
        """Creates a traverser from the root of the attribute path"""
        return cls(reference=AttributePath(path=[]), initial_value=initial_value)

    @classmethod
    def from_reference(
        cls,
        reference: AttributePath,
        initial_value="",
        parent_traverser: "AttributePathTraverser | None" = None,
    ):
        """Creates a traverser from an AttributePath reference"""
        if parent_traverser:
            reference = parent_traverser.create_scoped_reference(reference)

        return cls(reference=reference, initial_value=initial_value)

    def __init__(self, reference: AttributePath, initial_value=""):
        self.reference = reference
        self.index = 0
        self.alias_stack: list[str] = [initial_value]

    def next(self):
        if self.index >= len(self.reference.columns) - 1:
            return False

        self.alias_stack.append(
            self._generate_alias(
                self.alias_stack[-1],
                self.current_model_name,
                self.current_attribute_name,
            )
        )
        self.index += 1
        return True

    def prev(self):
        if self.index == 0:
            return False
        self.alias_stack.pop()
        self.index -= 1
        return True

    def _generate_alias(self, prev_alias: str, current_table: str, column: str = ""):
        m = hashlib.md5()
        m.update(prev_alias.encode("utf-8"))
        m.update(current_table.encode("utf-8"))
        if column:
            m.update(column.encode("utf-8"))
        return f"{current_table}_{m.hexdigest()[:8]}"

    def alias(self, model_name: str):
        """Creates an alias at the given traverser position"""
        return self._generate_alias(self.alias_stack[-1], model_name)

    def copy(self):
        """Creates a copy of the traverser"""
        traverser = AttributePathTraverser(
            reference=self.reference,
            initial_value=self.alias_stack[-1],
        )
        traverser.index = self.index
        traverser.alias_stack = self.alias_stack[:]
        return traverser

    def create_scoped_reference(self, reference: AttributePath) -> AttributePath:
        """Creates a scoped reference for the given model and column"""
        if self.index == 0:
            return reference
        else:
            new_ref = self.reference.path[: self.index]
            new_ref.extend(reference.path)
            return AttributePath(path=new_ref)

    @property
    def current_table_alias(self):
        return self.alias(self.current_model_name)

    @property
    def current_model_name(self):
        return self.reference.columns[self.index].table

    @property
    def current_attribute_name(self):
        return self.reference.columns[self.index].name

    def is_valid_for_registry(self, registry: Registry):
        """Checks if the reference is valid for the given registry"""

        # The final attribute must be a dimension or metric so we only iterate
        # through the relationships if we are not at the end of the reference
        if len(self.reference.columns) > 1:
            current_model = registry.get_model(self.current_model_name)
            current_attribute = current_model.get_attribute(self.current_attribute_name)
            # Only relationships can be traversed any other kind of attribute is
            # invalid
            if not isinstance(current_attribute, BoundRelationship):
                raise InvalidAttributeReferenceError(self.reference)
            while self.next():
                pass
        current_model = registry.get_model(self.current_model_name)
        current_attribute = current_model.get_attribute(self.current_attribute_name)
        if isinstance(current_attribute, BoundRelationship):
            raise InvalidAttributeReferenceError(self.reference)
        return True

    def to_end(self):
        """Moves the traverser to the end of the reference"""
        while self.next():
            pass
        return self
    

class SemanticQuery(BaseModel):
    """Used for serialization of semantic queries"""

    name: str = Field(
        default="", description="Optional name used to identify the query"
    )

    description: str = Field(
        default="", description="A description of the query's intent and purpose."
    )

    selects: t.List[str] = Field(
        description=textwrap.dedent(
            """
        A list of model attributes to select in the query. These should only be
        valid dimensions or measures from the available models in the registry.
        Joins are automatically handled by the query builder based on the
        provided attributes and the relationships defined in the models. If any
        ambiguous relationships between models should use the `->` syntax to
        specify the path through the relationships.
    """
        )
    )
    filters: t.List[str] = Field(
        description=textwrap.dedent(
            """
        A list of filters to apply to the query. These should be valid
        expressions that can be used to filter the results. The expressions can
        reference model attributes just like the columns. If any ambiguous
        relationships between models should use the `->` syntax to specify the
        path through the relationships.
    """
        ),
        default_factory=lambda: [],
    )

    limit: int = Field(
        default=0,
        description=textwrap.dedent(
            """
            The maximum number of rows to return in the query. If set to 0, no
            limit is applied.
        """
        ),
    )