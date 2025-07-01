from __future__ import annotations

import hashlib
import textwrap
import typing as t
from collections import deque
from enum import Enum
from graphlib import TopologicalSorter

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

from .errors import InvalidAttributeReferenceError
from .utils import exp_to_str, hash_expressions


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
    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: "Registry",
    ) -> "QueryPart":
        """Returns the QueryPart for the bound query part"""
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

    def query(self, query: "SemanticQuery") -> exp.Expression:
        """Returns the SQL query for the given query"""
        # Get the columns and filters from the query
        return query.sql(self)

    def describe(self) -> str:
        """Returns a description of the registry used for an LLM prompt"""

        description = "This is the semantic model available to query\n"

        description += "# All Available Models\n"
        for model in self.models.values():
            description += model.describe() + "\n"

        return description


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
    query: str = ""

    @model_validator(mode="after")
    def process_metric(self):
        expression = parse_one(self.query)
        result = AttributePathTransformer.transform(expression, self_model_name="self")
        self._expression = expression

        self._attribute_references = result.references
        return self

    def query_as_expression(self) -> exp.Expression:
        """Returns the SQL expression for the metric"""
        return self._expression

    def attribute_references(self) -> t.List["AttributePath"]:
        """Returns the references for model attributes"""
        return self._attribute_references

    def bind(self, model: "Model") -> "BoundMeasure":
        """Returns the bound metric for the given model"""

        return BoundMeasure(
            model=model,
            measure=self,
        )


class BoundMeasure:
    model: "Model"
    measure: Measure

    def __init__(self, model: "Model", measure: Measure):
        self.model = model
        self.measure = measure

    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: Registry,
    ) -> "QueryPart":
        """Returns the SQL expression for the measure"""

        query = self.measure.query_as_expression()
        result = AttributePathTransformer.transform(
            query, traverser.copy(), self_model_name=self.model.name
        )

        return QueryPart(
            registry=registry,
            original=original,
            expression=result.node,
            is_aggregate=True,
            resolved_references=result.references,
        )


class Filter(BaseModel):
    query: str

    def as_expression(self) -> exp.Expression:
        """Returns the SQL expression for the filter"""
        return parse_one(self.query)

    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: Registry,
    ) -> "QueryPart":
        result = AttributePathTransformer.transform(
            self.as_expression(), traverser=traverser, registry=registry
        )

        # Resolve the references to model attributes. If the attribute is a
        # measure then this is an aggregation.
        for reference in result.references:
            attribute = reference.final_attribute()
            model_name = exp_to_str(attribute.table)
            attribute_name = exp_to_str(attribute.this)
            model = registry.get_model(model_name)

            try:
                if isinstance(model.get_attribute(attribute_name), BoundMeasure):
                    # If the attribute is a measure, we need to treat it as an aggregate
                    # function. This means we need to use a subquery to calculate the
                    # measure before applying the filter.
                    return QueryPart(
                        registry=registry,
                        original=original,
                        expression=result.node,
                        is_aggregate=True,
                        resolved_references=result.references,
                    )
            except ValueError:
                # HACK. This means the attribute is a column... hopefully
                pass

        return QueryPart(
            registry=registry,
            original=original,
            expression=result.node,
            is_aggregate=False,
            resolved_references=result.references,
        )


class Dimension(BaseModel):
    """A dimension is a column or expression that must resolve to a column in
    the table.

    The dimension can either be a simple column reference or a non-aggregating
    expression.
    """

    name: str
    description: str = ""
    query: str = ""
    column_name: str = ""

    @model_validator(mode="after")
    def process_dimension(self):
        if self.query and self.column_name:
            raise ValueError("Cannot specify both query and column_name for dimension")
        if not self.query and not self.column_name:
            self.column_name = self.name

        if self.query:
            expression = parse_one(self.query)
        else:
            expression = exp.Column(
                table=exp.to_identifier("self"),
                this=exp.to_identifier(self.column_name),
            )

        # find all references in the expression
        result = AttributePathTransformer.transform(expression, self_model_name="self")
        self._expression = expression

        # Ensure all references point to self
        for ref in result.references:
            if ref.base_model != "self":
                raise ValueError(
                    f"Dimension {self.name} cannot reference another model. Found reference to {ref.base_model}. Only use `self`"
                )
        self._attribute_references = result.references

        return self

    def as_expression(self) -> exp.Expression:
        return self._expression

    def attribute_references(self) -> t.List["AttributePath"]:
        return self._attribute_references

    def bind(self, model: "Model") -> "BoundDimension":
        return BoundDimension(
            model=model,
            dimension=self,
        )


class BoundDimension:
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: "Model"
    dimension: Dimension

    def __init__(self, model: "Model", dimension: Dimension):
        self.model = model
        self.dimension = dimension

    def with_alias(self, alias: str) -> exp.Expression:
        """Returns the SQL expression for the dimension with the given alias"""
        query = self.query

        def transform_columns(node: exp.Expression):
            if isinstance(node, exp.Column):
                if isinstance(node.table, exp.Identifier) and node.table.this != "self":
                    raise ValueError(
                        "Cannot reference another model in a dimension. Use `self` as the table alias for the model"
                    )
                return exp.Column(
                    table=exp.to_identifier(alias),
                    this=node.this,
                )
            return node

        return query.transform(transform_columns)

    @property
    def query(self) -> exp.Expression:
        """Returns the SQL expression for the dimension"""
        return self.dimension.as_expression()

    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: Registry,
    ) -> "QueryPart":
        """Returns the QueryPart"""

        # table_alias = traverser.alias(self.model.name)

        query = self.dimension.as_expression()
        result = AttributePathTransformer.transform(
            query, traverser=traverser, self_model_name=self.model.name
        )

        return QueryPart(
            registry=registry,
            original=original,
            expression=result.node,
            is_aggregate=False,
            resolved_references=result.references,
        )


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

        # Topologically sort the dimensions
        attribute_graph: t.Dict[str, t.Set[str]] = {}
        for dimension in self.dimensions:
            if dimension.name in attribute_graph:
                raise ValueError(
                    f"Dimension {dimension.name} already exists in model {self.name}"
                )
            references = dimension.attribute_references()

            attribute_graph[dimension.name] = set()

            for relationship in references:
                if relationship.is_relationship() or relationship.base_model != "self":
                    raise ValueError("Cannot reference a relationship in a dimension")
                # Attribute/Column name
                attribute_name = exp_to_str(relationship.final_attribute().this)

                if attribute_name == dimension.name:
                    # If the attribute name is the same as the dimension name, we can skip it.
                    # For a dimension this just means that the dimension is a column in the table
                    continue

                attribute_graph[dimension.name].add(
                    exp_to_str(relationship.final_attribute().this)
                )

            attributes[dimension.name] = dimension.bind(self)

        # Check for cycles in the dimensions
        dimensions_sorter = TopologicalSorter(attribute_graph)
        dimensions_sorter.prepare()

        # Check for cycles in the measures and dimensions
        # For now this only checks for cycles in the current model.
        for metric in self.measures:
            # Ensure we don't have duplicate names
            if metric.name in attributes or metric.name in attribute_graph:
                raise ValueError(
                    f"Measure {metric.name} already exists in model {self.name}"
                )
            attribute_graph[metric.name] = set()
            for relationship in metric.attribute_references():
                if relationship.is_relationship() or relationship.base_model != "self":
                    continue  # Relationships are handled at query time (for now)
                attribute_graph[metric.name].add(
                    exp_to_str(relationship.final_attribute().this)
                )

            attributes[metric.name] = metric.bind(self)

        # Ensure we have no cycles
        attribute_sorter = TopologicalSorter(attribute_graph)
        attribute_sorter.prepare()

        self._model_ref_lookup_by_model_name: dict[str, list[Relationship]] = {}
        for relationship in self.relationships:
            if relationship.name in attributes:
                raise ValueError(
                    f"{relationship.name} already exists in model {self.name}. Must be unique"
                )

            attributes[relationship.name] = relationship.bind(self)

            if relationship.ref_model not in self._model_ref_lookup_by_model_name:
                self._model_ref_lookup_by_model_name[relationship.ref_model] = []
            self._model_ref_lookup_by_model_name[relationship.ref_model].append(
                relationship
            )

        self._all_attributes = attributes

        if isinstance(self.primary_key, str):
            self._primary_key_expression = coerce_to_tables_column(self.primary_key)
        elif isinstance(self.primary_key, list):
            self._primary_key_expression = hash_expressions(
                *[coerce_to_tables_column(pk) for pk in self.primary_key]
            )

        return self

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

    def resolve_dimension_with_alias(self, name: str, alias: str):
        """Returns the dimension with the given name and alias"""
        dimension = self.get_dimension(name)

        return dimension.with_alias(alias)

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

    def traverser(self, initial_value: str = ""):
        return AttributePathTraverser(self, initial_value=initial_value)

    @property
    def base_model(self):
        return self._columns[0].table

    @property
    def columns(self):
        return self._columns

    def resolve(
        self,
        registry: Registry,
        parent_traverser: "AttributePathTraverser | None" = None,
    ):
        traverser = self.traverser()
        while traverser.next():
            pass
        current_model = registry.get_model(traverser.current_model_name)
        current_attribute = current_model.get_attribute(
            traverser.current_attribute_name
        )
        match current_attribute:
            case BoundDimension():
                part = current_attribute.to_query_part(traverser.copy(), self, registry)
            case BoundMeasure():
                part = current_attribute.to_query_part(traverser.copy(), self, registry)
            case BoundRelationship():
                raise InvalidAttributeReferenceError(
                    self, "final attribute cannot be a relationship"
                )
        if parent_traverser:
            part = part.scope(parent_traverser)
        return part

    def resolve_child_references(
        self, registry: Registry, depth: int = 0
    ) -> list["AttributePath"]:
        """Resolves the child references for the given registry

        Measures can reference dimensions in related models. This resolves
        those references to the actual attributes in that other model.

        The depth is used to limit the number of levels to traverse. This is
        used to prevent infinite loops in the case of circular references.
        """
        traverser = self.traverser()
        while traverser.next():
            pass
        current_model = registry.get_model(traverser.current_model_name)
        current_attribute = current_model.get_attribute(
            traverser.current_attribute_name
        )
        match current_attribute:
            case BoundDimension():
                return [self]
            case BoundMeasure():
                # Recurse
                return [self]
            case BoundRelationship():
                raise InvalidAttributeReferenceError(
                    self, "final attribute cannot be a relationship"
                )
            case _:
                raise ValueError(
                    f"FATAL: unexpected attribute type {current_attribute} in model {current_model.name}"
                )

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


class AttributePathTransformer:
    """Provides a transformer that tracks attribute references in an expression
    and replaces them with macro functions that can be resolved at sql
    generation time

    Should be called with the `transform` class method.
    """

    @classmethod
    def parse_to_self_expression(
        cls, context: str, expression_str: str
    ) -> AttributeTransformerResult:
        """Parses an expression string to a SQL expression that references the self table."""
        expression = parse_one(expression_str)
        result = cls.transform(expression, self_model_name="self")

        # Ensure all references point to self
        for ref in result.references:
            if ref.base_model not in ["self", ""]:
                raise ValueError(
                    f"{context} cannot reference another model. Found reference to {ref.base_model}. Only use `self`"
                )

        # Remove $semantic_ref
        def transform_semantic_ref(node: exp.Expression):
            if (
                isinstance(node, exp.Anonymous)
                and exp_to_str(node.this) == "$semantic_ref"
            ):
                return exp.to_column(exp_to_str(node.expressions[0]))

            return node

        return AttributeTransformerResult(
            node=result.node.transform(transform_semantic_ref),
            references=result.references,
        )

    @classmethod
    def transform(
        cls,
        node: exp.Expression,
        traverser: "AttributePathTraverser | None" = None,
        self_model_name: str = "",
        registry: Registry | None = None,
    ):
        """Transform an expression and return a result that also contains the
        attribute references found in the expression"""

        transformer = cls(
            traverser=traverser, self_model_name=self_model_name, registry=registry
        )
        transformed_node = node.transform(transformer)

        return AttributeTransformerResult(
            node=transformed_node, references=transformer.references
        )

    def __init__(
        self,
        traverser: "AttributePathTraverser | None" = None,
        self_model_name: str = "",
        registry: Registry | None = None,
    ):
        self.references: list[AttributePath] = []
        self.self_model_name = self_model_name
        if traverser:
            self.traverser = traverser
        else:
            self.traverser = AttributePathTraverser(reference=AttributePath(path=[]))
        self.registry = registry

    def __call__(self, node: exp.Expression):
        if is_expression_attribute_reference(node):
            if isinstance(node, exp.Column):
                model_name = exp_to_str(node.table)
                column_name = exp_to_str(node.this)
                if model_name == "self":
                    # We have a self reference
                    if not self.self_model_name:
                        # TODO ... improve this error message
                        raise ValueError("Cannot use self reference in this expression")
                    model_name = self.self_model_name
                reference = AttributePath.from_string(f"{model_name}.{column_name}")
            else:
                # Check for self in reference path
                reference_path = node.sql(dialect="duckdb").split("->")
                for i in range(len(reference_path)):
                    ref = reference_path[i]
                    as_column = exp.to_column(ref)
                    model_name = exp_to_str(as_column.table)

                    if model_name == "self":
                        if not self.self_model_name:
                            # TODO ... improve this error message
                            raise ValueError(
                                "Cannot use self reference in this expression"
                            )
                        model_name = self.self_model_name
                        reference_path[i] = f"{model_name}.{exp_to_str(as_column.this)}"
                reference = AttributePath(path=reference_path)

            appended_reference = self.append_scoped_reference(reference)
            refs_as_literals = exp.Literal.string(str(appended_reference))

            # Check if the reference is to a model's attribute or to an actual column
            if self.registry:
                part = appended_reference.resolve(
                    self.registry, parent_traverser=self.traverser.copy()
                )
                for references in part.resolved_references:
                    self.references.append(references)
                return part.expression

            return exp.Anonymous(this="$semantic_ref", expressions=[refs_as_literals])
        return node

    def append_scoped_reference(self, reference: AttributePath):
        """Appends a reference to the transformer"""
        scoped_reference = self.traverser.create_scoped_reference(reference)
        self.references.append(scoped_reference)
        return scoped_reference


class QueryPart(BaseModel):
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
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    registry: Registry

    original: AttributePath | str

    expression: exp.Expression = Field(description="The final sql expression")

    is_aggregate: bool = Field(
        description="Whether the column is an aggregate function"
    )

    resolved_references: t.List[AttributePath] = Field(
        description="All of the resolved references for the attribute resolved for the current registry"
    )

    @property
    def is_additive(self):
        """Whether the column is additive"""
        return self.is_aggregate

    def scope(self, traverser: "AttributePathTraverser") -> "QueryPart":
        """Scopes the query part to the given traverser"""
        scoped_references: list[AttributePath] = []

        def scope_semantic_refs(node: exp.Expression):
            if (
                isinstance(node, exp.Anonymous)
                and exp_to_str(node.this).lower() == "$semantic_ref"
            ):
                # Replace the reference with the scoped reference
                current_reference = AttributePath.from_string(
                    exp_to_str(node.expressions[0])
                )
                scoped_reference = traverser.create_scoped_reference(current_reference)
                scoped_references.append(scoped_reference)
                return exp.Anonymous(
                    this="$semantic_ref",
                    expressions=[exp.Literal.string(str(scoped_reference))],
                )
            return node

        scoped_expression = self.expression.transform(scope_semantic_refs)

        return QueryPart(
            registry=self.registry,
            original=self.original,
            expression=scoped_expression,
            is_aggregate=self.is_aggregate,
            resolved_references=scoped_references,
        )


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

    def current_column(self, registry: Registry):
        """Returns the current column in the traverser"""
        model = registry.get_model(self.current_model_name)

        attribute = model.get_attribute(self.current_attribute_name)

        match attribute:
            case BoundDimension():
                return attribute.with_alias(self.current_table_alias)
            case BoundMeasure():
                raise NotImplementedError("Cannot resolve a metric to a column")
            case BoundRelationship():
                raise ValueError(
                    f"Cannot use relationship {self.current_attribute_name} in traverser"
                )

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


class SemanticQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    @model_validator(mode="after")
    def process_selects(self):
        self._processed_selects: t.List[t.Tuple[AttributePath, str]] = []
        for select in self.selects:
            result = AttributePathTransformer.transform(parse_one(select))
            if len(result.references) != 1:
                raise ValueError(
                    f"Invalid column reference {select}. Must be a single reference with an optional alias"
                )
            if not isinstance(result.node, (exp.Anonymous, exp.Alias)):
                raise ValueError(
                    f"Invalid column reference {select}. Must be a single reference with an optional alias"
                )
            column_path = result.references[0]
            alias = column_path.to_select_alias()
            if isinstance(result.node, exp.Alias):
                alias = exp_to_str(result.node.alias)

            self._processed_selects.append((column_path, alias))

        self._processed_filters = [Filter(query=f) for f in self.filters]

        return self

    def sql(self, registry: Registry):
        from .query import QueryBuilder

        query = QueryBuilder(registry)
        query.select(*self.selects)
        query.where(*self.filters)
        query.add_limit(self.limit)
        return query.build()

    def analyze(self, registry: Registry):
        """Validates the query against the registry to ensure the query can be executed

        Returns a set of suggestions to the user on how to fix the query
        """
        pass


# class ParameterizedSemanticQuery(BaseModel):
#     model_config = ConfigDict(arbitrary_types_allowed=True)

#     input_vars: t.List[str] = Field(default_factory=lambda: [])
#     description: str = ""
#     columns: t.List[str | exp.Column | t.Callable[..., str | exp.Column]] = Field(
#         default_factory=lambda: []
#     )
#     filters: t.List[str | exp.Expression | t.Callable[..., str | exp.Expression]] = (
#         Field(default_factory=lambda: [])
#     )

#     generators: t.Dict[str, t.List[t.Any]] = Field(default_factory=lambda: {})

#     def __call__(
#         self, inputs: t.Optional[t.Dict[str, t.List[t.Any]]]
#     ) -> t.Sequence[SemanticQuery]:
#         # using the inputs calculate the actual columns
#         # Convert query into it's generated queries

#         if not inputs:
#             return [
#                 SemanticQuery(
#                     columns=self.process_columns({}),
#                     filters=self.process_filters({}),
#                 )
#             ]
#         permutations = reduce(
#             lambda x, y: x * y, map(lambda x: len(x), inputs.values()), 1
#         )
#         key_order = list(inputs.keys())

#         count = 0
#         generated: t.List[SemanticQuery] = []
#         while count < permutations:
#             key_indices = {k: 0 for k in key_order}
#             key_index_calc = count
#             for key in key_order:
#                 key_indices[key] = key_index_calc % len(inputs[key])
#                 key_index_calc = key_index_calc // len(inputs[key])
#             inputs = {k: v[key_indices[k]] for k, v in inputs.items()}
#             generated.append(
#                 SemanticQuery(
#                     columns=self.process_columns(inputs),
#                     filters=self.process_filters(inputs),
#                 )
#             )
#         return generated

#     def process_filters(self, inputs: t.Dict[str, t.Any]) -> t.List[exp.Expression]:
#         filters: t.List[exp.Expression] = []
#         for filter in self.filters:
#             if callable(filter):
#                 filter = filter(**inputs)
#             if isinstance(filter, str):
#                 filter = parse_one(filter)
#             filters.append(filter)
#         return filters

#     def process_columns(
#         self, inputs: t.Dict[str, t.Any]
#     ) -> t.List[exp.Column | t.List[exp.Column]]:
#         columns: t.List[exp.Column | t.List[exp.Column]] = []
#         for column in self.columns:
#             if callable(column):
#                 column = column(**inputs)

#             if isinstance(column, str):
#                 if "->" in column:
#                     column = list(map(lambda a: exp.to_column(a), column.split("->")))
#                 else:
#                     column = exp.to_column(column)
#                 columns.append(column)
#             elif isinstance(column, exp.Expression):
#                 if isinstance(column, exp.Column):
#                     columns.append(column)
#                 else:
#                     raise ValueError(f"Unsupported expression {column}")
#         return columns


class EntityConnector(ViewConnector):
    def primary_key(self, model_name) -> t.Optional[str | exp.Expression]:
        return f"{model_name}_id"

    def dimensions(self, model_name) -> t.List[Dimension]:
        return [
            Dimension(
                name="id",
                description="The unique identifier of an entity",
                query=f"{model_name}_id",
            ),
            Dimension(
                name="name",
                description="The type of the entity",
                query=f"{model_name}_name",
            ),
            Dimension(
                name="namespace",
                description="The namespace of the entity",
                query=f"{model_name}_namespace",
            ),
        ]
