import hashlib
import typing as t
from enum import Enum
from graphlib import TopologicalSorter

from metrics_tools.semantic.errors import InvalidAttributeReferenceError
from metrics_tools.utils.glot import exp_to_str
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlglot import exp
from sqlmesh.core.dialect import parse_one


class RegistryDAG:
    """A DAG of models and views that can be used to generate SQL queries.

    This is used to determine the order in which models and views should be
    """

    adjacency_map: t.Dict[str, t.Set[str]]
    ancestor_depth: t.Dict[str, int]
    sorted_model_names: t.List[str] | None
    sorter: TopologicalSorter[str]

    def __init__(self):
        self.adjacency_map = {}
        self.sorted_model_names = None
        self.ancestor_depth = {}
        self.sorter = TopologicalSorter()

    def add(self, model: "Model"):
        """Inserts the model into the registry and updates the adjacency map.

        Cycles are not allowed in the registry. If a cycle is detected, an error
        will be raised on later calls
        """

        # Register the model under the given name
        self.adjacency_map[model.name] = set()

        # Gets all the names of related models
        reference_names = list(map(lambda x: x.model_ref, model.references))

        self.sorter.add(model.name, *reference_names)

        adj_set = self.adjacency_map.get(model.name, set())
        adj_set = adj_set.union(set(reference_names))
        self.adjacency_map[model.name] = adj_set

    def determine_ancestor_values(self):
        """Determines the ancestor values of the model and updates the adjacency map"""

        def get_ancestor_depth(name: str) -> int:
            depth = 0
            if name in self.ancestor_depth:
                return self.ancestor_depth[name]

            max_depth = 0
            for current_deps in self.adjacency_map.get(name, set()):
                depth = get_ancestor_depth(current_deps) + 1
                if depth > max_depth:
                    max_depth = depth
            return max_depth

        for model_name in self.topological_sort():
            self.ancestor_depth[model_name] = get_ancestor_depth(model_name)

    def get_ancestor_depth(self, name: str) -> int:
        if name not in self.ancestor_depth:
            raise ValueError(f"Model {name} not found in registry")
        return self.ancestor_depth[name]

    def depth_sorted_models(self, models: t.Collection[str], reverse: bool = False):
        """Sorts the models in depth order"""
        return sorted(models, key=lambda x: self.ancestor_depth[x], reverse=reverse)

    def upstream(self, name: str, include_self: bool = False) -> t.Set[str]:
        """Returns the upstream models of the given model"""

        def get_upstream(name: str) -> t.Set[str]:
            upstream = self.adjacency_map.get(name, set())
            for current_deps in upstream:
                upstream = upstream.union(get_upstream(current_deps))
            return upstream

        if include_self:
            return get_upstream(name).union({name})
        return get_upstream(name)

    def topological_sort(self):
        """Sort the models in topological order"""
        if not self.sorted_model_names:
            self.sorted_model_names = list(self.sorter.static_order())
        for name in self.sorted_model_names:
            yield name

    def join_paths(
        self, from_model: str, to_model: str
    ) -> t.Tuple[t.List[str], t.List[str]]:
        """Returns the shortest ordered paths between two models in the dag.

        This will always return two paths, one from the from_model to the join
        point and one from the join point to the to_model. The join point is the
        model that intersects the two paths. If the two models are the same,
        then the paths will be empty.
        """

        if from_model not in self.adjacency_map:
            raise ValueError(f"Model {from_model} not found in registry")
        if to_model not in self.adjacency_map:
            raise ValueError(f"Model {to_model} not found in registry")
        if from_model == to_model:
            return [], []

        # Get the upstream models of from_model
        from_upstream = self.upstream(from_model, True)

        # Get the upstream models of to_model
        to_upstream = self.upstream(to_model, True)

        # Get the intersection of the two sets
        intersection = from_upstream.intersection(to_upstream)
        if not intersection:
            raise ModelHasNoJoinPath(
                f"No path found between {from_model} and {to_model}"
            )
        # Sort the intersection by depth
        sorted_intersection = self.depth_sorted_models(intersection, True)

        # Get the first model in the intersection
        # This is the model that is closest to both models
        # and is the model that will be used to join the two models
        join_point = sorted_intersection[0]

        # Get the path from the from_model to the join point
        from_path = [from_model]
        if from_model != join_point:
            sorted_from_upstream = self.depth_sorted_models(from_upstream, True)
            for model in sorted_from_upstream[1:]:
                from_path.append(model)
                if model == join_point:
                    break

        # Get the path from the join point to the to_model
        to_path = [to_model]
        if to_model != join_point:
            sorted_to_upstream = self.depth_sorted_models(to_upstream, True)
            for model in sorted_to_upstream[1:]:
                to_path.append(model)
                if model == join_point:
                    break
        return from_path, to_path
    

class BoundModelAttribute(t.Protocol):
    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: "Registry",
    ) -> "QueryPart":
        """Returns the QueryPart for the bound query part"""
        ...
    

class UnboundModelAttribute(t.Protocol):
    def bind(self, model: "Model") -> "BoundModelAttribute":
        """Binds the query part to the given model and returns a QueryPart"""
        ...


class Registry:
    models: t.Dict[str, "Model"]
    dag: RegistryDAG
    views: t.Dict[str, "View"]
    completed: bool

    def __init__(self):
        self.models = {}
        self.views = {}
        self.sorted_model_names = None
        self.dag = RegistryDAG()
        self.completed = False

    def register(self, model: "Model", repoen: bool = False):
        """Inserts the model into the registry and updates the adjacency map.

        Cycles are not allowed in the registry. If a cycle is detected, an error
        will be raised on later calls
        """
        if self.completed and not repoen:
            raise ValueError(
                "Registry has already been completed cannot add new models"
            )

        self.models[model.name] = model
        # Register the model under the given name
        self.dag.add(model)

    def register_view(self, view: "View"):
        self.views[view.name] = view

    def get_model(self, name: str) -> "Model":
        return self.models[name]

    def get_view(self, name: str) -> "View":
        return self.views[name]

    def topological_sort(self):
        """Sort the models in topological order"""
        if not self.completed:
            raise ValueError("Registry has not been completed cannot sort models")

        yield from self.dag.topological_sort()

    def complete(self):
        """Completes the registry by determining the ancestor values of the models"""
        self.completed = True

        self.dag.determine_ancestor_values()

    def join_relationships(
        self, from_model: str, to_model: str, through_attribute: str = ""
    ) -> t.List["BoundRelationship"]:
        """Returns the join path between two models"""
        from_path, to_path = self.dag.join_paths(from_model, to_model)

        def build_join_path(
            model_path: t.List[str], via_attribute: str = ""
        ) -> t.List[BoundRelationship]:
            prev_model: Model | None = None
            join_path: t.List[BoundRelationship] = []
            for model_name in model_path:
                if prev_model is None:
                    via_attribute = via_attribute
                    prev_model = self.models[model_name]
                    continue

                relationship = prev_model.find_relationship(
                    name=via_attribute, model_ref=model_name
                )
                prev_model = self.models[model_name]
                join_path.append(relationship)
            return join_path

        from_path_joins = build_join_path(from_path, through_attribute)
        to_path_joins = build_join_path(to_path)

        return from_path_joins + to_path_joins

    def query(self, query: "SemanticQuery") -> exp.Expression:
        """Returns the SQL query for the given query"""
        # Get the columns and filters from the query
        return query.sql(self)


class MetricOperationType(str, Enum):
    """The type of operation to perform on the metric.

    This is used to determine how to aggregate the metric.
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


class Metric(BaseModel):
    name: str
    description: str = ""
    query: str = ""

    def query_as_expression(self) -> exp.Expression:
        """Returns the SQL expression for the metric"""
        return parse_one(self.query)

    def bind(self, model: "Model") -> "BoundMetric":
        """Returns the bound metric for the given model"""

        return BoundMetric(
            model=model,
            metric=self,
        )


class BoundMetric:
    model: "Model"
    metric: Metric

    def __init__(self, model: "Model", metric: Metric):
        self.model = model
        self.metric = metric

    def to_query_part(
        self,
        traverser: "AttributePathTraverser",
        original: "AttributePath | str",
        registry: Registry,
    ) -> "QueryPart":
        """Returns the SQL expression for the metric"""

        query = self.metric.query_as_expression()
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
            self.as_expression(), traverser=traverser
        )

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
        return self

    def as_expression(self) -> exp.Expression:
        if self.query:
            return parse_one(self.query)
        return exp.Column(
            table=exp.to_identifier("self"), this=exp.to_identifier(self.column_name)
        )

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
    MANY_TO_MANY = "many_to_many"


class Relationship(BaseModel):
    name: str = ""
    model_ref: str
    type: RelationshipType
    join_table: t.Optional[str] = None
    self_key_column: t.Optional[str] = None
    foreign_key_column: t.Optional[str] = None


class BoundRelationship:
    model: str
    name: str = ""
    model_ref: str
    type: RelationshipType
    join_table: t.Optional[str] = None
    self_key_column: t.Optional[str] = None
    foreign_key_column: t.Optional[str] = None

    def __init__(
        self,
        model: str,
        name: str,
        model_ref: str,
        type: RelationshipType,
        self_key_column: t.Optional[str] = None,
        foreign_key_column: t.Optional[str] = None,
        join_table: t.Optional[str] = None,
    ):
        self.model = model
        self.name = name
        self.model_ref = model_ref
        self.type = type
        self.self_key_column = self_key_column
        self.foreign_key_column = foreign_key_column
        self.join_table = join_table


class ViewConnector(BaseModel):
    def primary_key(self, model_name) -> t.Optional[str | exp.Expression]:
        return None

    def time_column(self, model_name) -> t.Optional[str]:
        return None

    def dimensions(self, model_name) -> t.List[Dimension]:
        return []

    def metrics(self, model_name) -> t.List[Metric]:
        return []


class View(BaseModel):
    """A generic set of dimensions and metrics that can be queried together."""

    name: str
    description: str = ""
    connector: ViewConnector


class Model(BaseModel):
    name: str
    description: str = ""
    table: str

    primary_key: str = ""
    time_column: t.Optional[str] = None

    # These are additional interfaces to the model
    views: t.List[View | str] = Field(default_factory=lambda: [])

    dimensions: t.List[Dimension] = Field(default_factory=lambda: [])
    metrics: t.List[Metric] = Field(default_factory=lambda: [])
    references: t.List[Relationship] = Field(default_factory=lambda: [])

    @model_validator(mode="after")
    def build_reference_lookup(self):
        """Builds a lookup of the references in the model"""
        attributes: dict[str, BoundDimension | BoundMetric | BoundRelationship] = {}

        for dimension in self.dimensions:
            # Ensure we don't have duplicate names
            if dimension.name in attributes:
                raise ValueError(
                    f"Dimension {dimension.name} already exists in model {self.name}"
                )
            attributes[dimension.name] = dimension.bind(self)

        for metric in self.metrics:
            # Ensure we don't have duplicate names
            if metric.name in attributes:
                raise ValueError(
                    f"Metric {metric.name} already exists in model {self.name}"
                )
            attributes[metric.name] = metric.bind(self)

        self._model_ref_lookup_by_model_name: dict[str, list[Relationship]] = {}
        for reference in self.references:
            if reference.name in attributes:
                raise ValueError(
                    f"{reference.name} already exists in model {self.name}. Must be unique"
                )

            attributes[reference.name] = BoundRelationship(
                model=self.name,
                name=reference.name,
                model_ref=reference.model_ref,
                type=reference.type,
                self_key_column=reference.self_key_column,
                foreign_key_column=reference.foreign_key_column,
                join_table=reference.join_table,
            )

            if reference.model_ref not in self._model_ref_lookup_by_model_name:
                self._model_ref_lookup_by_model_name[reference.model_ref] = []
            self._model_ref_lookup_by_model_name[reference.model_ref].append(reference)

        self._all_attributes = attributes

        return self

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
            for reference in self.references:
                if reference.name == name:
                    if reference.model_ref != model_ref:
                        raise ValueError(
                            f"Reference {name} does not match model_ref {model_ref}"
                        )
                    return self.get_relationship(name)

        for reference in self.references:
            references = self._model_ref_lookup_by_model_name[reference.model_ref]
            if len(references) > 1:
                raise ModelHasAmbiguousJoinPath(
                    f"Reference {model_ref} is ambiguous in model {self.name}"
                )
            if reference.model_ref == model_ref:
                relationship = self._all_attributes[reference.name]
                if not isinstance(relationship, BoundRelationship):
                    raise ValueError(
                        f"{reference.name} is not a reference in model {self.name}"
                    )
                return relationship
        raise ValueError(f"Reference {name} not found in model {self.name}")

    @property
    def table_exp(self):
        """Returns the table for the model"""
        return exp.to_table(self.table)

    def get_attribute(
        self, name: str
    ) -> BoundDimension | BoundMetric | BoundRelationship:
        """Resolves the attribute to a column in the model"""
        if name not in self._all_attributes:
            raise ValueError(f"Attribute {name} not found in model {self.name}")
        return self._all_attributes[name]

    def resolve_dimension_with_alias(self, name: str, alias: str):
        """Returns the dimension with the given name and alias"""
        dimension = self.get_dimension(name)

        return dimension.with_alias(alias)


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

    def resolve(self, registry: Registry):
        traverser = self.traverser()
        while traverser.next():
            pass
        current_model = registry.get_model(traverser.current_model_name)
        current_attribute = current_model.get_attribute(
            traverser.current_attribute_name
        )
        match current_attribute:
            case BoundDimension():
                return current_attribute.to_query_part(traverser.copy(), self, registry)
            case BoundMetric():
                return current_attribute.to_query_part(traverser.copy(), self, registry)
            case BoundRelationship():
                raise InvalidAttributeReferenceError(
                    self, "final attribute cannot be a relationship"
                )

    def resolve_child_references(
        self, registry: Registry, depth: int = 0
    ) -> list["AttributePath"]:
        """Resolves the child references for the given registry

        Metrics can reference dimensions in related models. This resolves
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
            case BoundMetric():
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

    def __eq__(self, other: object) -> bool:
        """Checks if the reference is equal to another reference"""
        if not isinstance(other, AttributePath):
            return False
        return self.path == other.path
    
    def final_attribute(self) -> exp.Column:
        """Returns the final column in the reference"""
        return self._columns[-1]
    
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
    def transform(
        cls,
        node: exp.Expression,
        traverser: "AttributePathTraverser | None" = None,
        self_model_name: str = "",
        registry: Registry | None = None,
    ):
        """Transform an expression and return a result that also contains the
        attribute references found in the expression"""

        transformer = cls(traverser=traverser, self_model_name=self_model_name, registry=registry)
        transformed_node = node.transform(transformer)

        return AttributeTransformerResult(
            node=transformed_node, references=transformer.references
        )

    def __init__(
        self, traverser: "AttributePathTraverser | None" = None, self_model_name: str = "", registry: Registry | None = None
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
                reference = AttributePath.from_string(
                    f"{model_name}.{column_name}"
                )
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
            refs_as_literals = str(appended_reference)

            # Check if the reference is to a model's attribute or to an actual column
            # if self.registry:
            #     part = appended_reference.resolve(self.registry)
                # final_attribute = appended_reference.final_attribute()
                # final_model_name = exp_to_str(final_attribute.table)
                # if final_model_name == "self":
                #     final_model_name = self.self_model_name
                # final_attribute_name = exp_to_str(final_attribute.this)
                # final_model = self.registry.get_model(final_model_name)
                # try:
                #     final_attribute_val = final_model.get_attribute(
                #         final_attribute_name
                #     )
                # except ValueError:
                #     # We assume this is an actual column
                #     pass

            return exp.Anonymous(this="$semantic_ref", expressions=[refs_as_literals])
        return node

    def append_scoped_reference(self, reference: AttributePath):
        """Appends a reference to the transformer"""
        scoped_reference = self.traverser.create_scoped_reference(reference)
        self.references.append(scoped_reference)
        return scoped_reference
    

class QueryPart(BaseModel):
    """The most basic representation of a part of a query.

    This is used to represent dimensions, metrics, and filters in a query.

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


class AttributePathTraverser:
    """AttributeReferences are used to reference a dimension or metric in a
    model.

    Because some models may reference another model more than once. The way this
    would be distinguished would be through different foreign key columns.
    Reference traversal, tracks the joins through these columns. We do this by
    enabling joins through a specific column.

    The following table shows how a traverser works, given a reference
    `a.b->c.d->e.f`:

    | Index             | 0      | 1               | 2                        |
    |-------------------|--------|-----------------|--------------------------|
    | Through Column    | a.b    | c.d             | e.f                      |
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

    def create_scoped_reference(
        self, reference: AttributePath
    ) -> AttributePath:
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
            case BoundMetric():
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

    columns: t.List[str]
    filters: t.List[str] = Field(default_factory=lambda: [])

    limit: int = 0

    @model_validator(mode="after")
    def process_columns(self):
        # Bit of a circular dependency but makes this easier to work with
        self._processed_columns = [
            AttributePath.from_string(col) for col in self.columns
        ]
        self._processed_filters = [Filter(query=f) for f in self.filters]

        return self

    def sql(self, registry: Registry):
        from metrics_tools.semantic.query import QueryBuilder

        query = QueryBuilder(registry)
        for column in self._processed_columns:
            query.add_select(column)
        for filter in self._processed_filters:
            query.add_filter(filter)
        query.add_limit(self.limit)
        return query.build()


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
