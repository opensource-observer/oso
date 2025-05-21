import hashlib
import typing as t
from collections.abc import Sequence
from enum import Enum
from functools import reduce
from graphlib import TopologicalSorter

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

        This will always return two paths, one from the from_model to the join point
        and one from the join point to the to_model. The join point is the model that intersects the two paths.
        If the two models are the same, then the paths will be empty.
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
    ) -> t.List["ModelBoundRelationship"]:
        """Returns the join path between two models"""
        from_path, to_path = self.dag.join_paths(from_model, to_model)

        def build_join_path(
            model_path: t.List[str], via_attribute: str = ""
        ) -> t.List[ModelBoundRelationship]:
            prev_model: Model | None = None
            join_path: t.List[ModelBoundRelationship] = []
            for model_name in model_path:
                if prev_model is None:
                    via_attribute = via_attribute
                    prev_model = self.models[model_name]
                    continue

                relationship = prev_model.get_relationship(
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


class Metric(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""
    query: str | exp.Expression
    filters: t.Optional[str | exp.Expression] = None


class Dimension(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""
    query: t.Optional[str | exp.Expression | t.Callable[..., exp.Expression]] = None


class RelationshipType(str, Enum):
    """The type of reference to use for the model.

    This is used to determine how to join the models together.
    """

    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"


class Relationship(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    model_ref: str
    type: RelationshipType
    via: t.Optional[str] = None
    self_key_column: t.Optional[str] = None
    foreign_key_column: t.Optional[str] = None


class ModelBoundRelationship(BaseModel):
    model: str
    name: str = ""
    model_ref: str
    type: RelationshipType
    via: t.Optional[str] = None
    self_key_column: t.Optional[str] = None
    foreign_key_column: t.Optional[str] = None


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
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str = ""

    primary_key: str | exp.Expression | t.List[str] | t.List[exp.Expression]
    time_column: t.Optional[str] = None

    # These are additional interfaces to the model
    views: t.List[View | str] = Field(default_factory=lambda: [])

    dimensions: t.List[Dimension] = Field(default_factory=lambda: [])
    metrics: t.List[Metric] = Field(default_factory=lambda: [])
    references: t.List[Relationship] = Field(default_factory=lambda: [])

    @model_validator(mode="after")
    def build_reference_lookup(self):
        """Builds a lookup of the references in the model"""
        self._dimension_lookup: t.Dict[str, Dimension] = {
            dimension.name: dimension for dimension in self.dimensions
        }
        self._model_ref_lookup: t.Dict[str, t.List[Relationship]] = {}
        for reference in self.references:
            if reference.model_ref not in self._model_ref_lookup:
                self._model_ref_lookup[reference.model_ref] = []
            self._model_ref_lookup[reference.model_ref].append(reference)

        return self

    def get_dimension(self, name: str) -> Dimension:
        """Returns the dimension with the given name"""
        if name not in self._dimension_lookup:
            raise ValueError(f"Dimension {name} not found in model {self.name}")
        return self._dimension_lookup[name]

    @property
    def table(self) -> str:
        """Returns the table name for the model"""
        return self.name

    def get_relationship(
        self, *, model_ref: str, name: str = ""
    ) -> "ModelBoundRelationship":
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
                    return ModelBoundRelationship(
                        model=self.name,
                        name=reference.name,
                        model_ref=reference.model_ref,
                        type=reference.type,
                        self_key_column=reference.self_key_column,
                        foreign_key_column=reference.foreign_key_column,
                        via=reference.via,
                    )

        for reference in self.references:
            references = self._model_ref_lookup[reference.model_ref]
            if len(references) > 1:
                raise ModelHasAmbiguousJoinPath(
                    f"Reference {model_ref} is ambiguous in model {self.name}"
                )
            if reference.model_ref == model_ref:
                return ModelBoundRelationship(
                    model=self.name,
                    name=reference.name,
                    model_ref=reference.model_ref,
                    type=reference.type,
                    self_key_column=reference.self_key_column,
                    foreign_key_column=reference.foreign_key_column,
                    via=reference.via,
                )
        raise ValueError(f"Reference {name} not found in model {self.name}")


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


class QueryColumnDAG:
    def __init__(self):
        self._columns_graph: t.Dict[str, t.Set[str]] = {}
        self._vias: t.Dict[str, str] = {}
        self._select_columns: list[str] = []

    def add_column(self, column: exp.Column):
        """Adds a column to the registry"""

        # Shouldn't add any deps for the column
        node = self._columns_graph.get(f"{column.table}.{column.name}", set())
        self._columns_graph[f"{column.table}.{column.name}"] = node

        self._select_columns.append(f"{column.table}.{column.name}")

    def add_column_with_via(self, columns: t.List[exp.Column]):
        prev = None
        for column in columns:
            node = self._columns_graph.get(f"{column.table}.{column.name}", set())
            if prev:
                node.add(f"{prev.table}.{prev.name}")
            self._columns_graph[f"{column.table}.{column.name}"] = node
            prev = column


class AttributeReference(BaseModel):
    ref: list[str]

    @model_validator(mode="after")
    def process_ref(self):
        self._columns = [exp.to_column(r) for r in self.ref]
        return self

    @classmethod
    def from_string(cls, ref: str) -> "AttributeReference":
        return cls(ref=ref.split("->"))

    def traverser(self):
        return ReferenceTraverser(self)

    @property
    def base_model(self):
        return self._columns[0].table

    @property
    def columns(self):
        return self._columns

    @property
    def as_column(self):
        traverser = self.traverser()
        while traverser.next():
            pass
        return traverser.current_column


class ReferenceTraverser:
    """AttributeReferences are used to reference a dimension or metric in a
    model.

    Because some models may reference another model more than once. The way this
    would be distinguished would be through different foreign key columns.
    Reference traversal, tracks the joins through these columns. We do this by
    enabling joins through a specific column.

    The following table shows how a traverser works, given a reference
    `a.b->c.d->e.f`

    Index             | 0      | 1               | 2                         |
    --------------------------------------------------------------------------
    Through Column    | a.b    | c.d             | e.f                       |
    Alias for table g | md5(g) | md5(md5(a.b)+g) | md5(md5(md5(a.b)+c.d)+g)  |

    This allows us to ensure that we don't duplicate joins by ensuring that each
    level through a given column reference uses the same table alias.

    """

    def __init__(self, reference: AttributeReference, initial_value=""):
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
                self.current_column.name,
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

    @property
    def current_table_alias(self):
        return self.alias(self.current_model_name)

    @property
    def current_model_name(self):
        return self.reference.columns[self.index].table

    @property
    def current_column(self):
        return exp.Column(
            table=exp.to_identifier(self.current_table_alias),
            this=exp.to_identifier(self.reference.columns[self.index].name),
        )


class SemanticQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    columns: t.List[exp.Column | t.List[exp.Column]]
    filters: t.List[exp.Expression] | None = None

    @model_validator(mode="after")
    def process_columns(self):
        required_tables: set[str] = set()
        vias_map: dict[str, t.List[t.List[exp.Column]]] = {}
        select_columns: t.List[exp.Column] = []

        # get the required tables for the query
        columns = self.columns
        for column in columns:
            # If it's a sequence then this will require joins
            if isinstance(column, Sequence):
                base_via = column[0]
                vias = vias_map.get(base_via.table, [])
                vias.append(column)
                vias_map[base_via.table] = vias

                final_column = column[-1]
                table = final_column.table
                select_columns.append(final_column)
            else:
                table = column.table
                select_columns.append(column)
            required_tables.add(table)

        self._vias = vias_map

        return self

    def sql(self, registry: Registry):
        # multiple vias on the same model mean we need to do some ctes
        # as long as there aren't multiple vias then we can just do a single join

        columns = self.columns
        required_tables: set[str] = set()
        vias_map: dict[str, t.List[t.List[exp.Column]]] = {}
        select_columns: t.List[exp.Column] = []

        # get the required tables for the query
        for column in columns:
            # If it's a sequence then this will require joins
            if isinstance(column, Sequence):
                base_via = column[0]
                vias = vias_map.get(base_via.table, [])
                vias.append(column)
                vias_map[base_via.table] = vias

                final_column = column[-1]
                table = final_column.table
                select_columns.append(final_column)
            else:
                table = column.table
                select_columns.append(column)
            required_tables.add(table)

        # Get deepest table and use that as the base table
        # This is the table that will be used to join all the other tables
        # together
        sorted_tables = registry.dag.depth_sorted_models(required_tables, reverse=True)
        base_table = sorted_tables[0]

        already_joined_tables = set()

        # Starting at the base table we will join all other tables together
        # using the join paths
        query = exp.select(*select_columns).from_(base_table)
        if len(sorted_tables) > 1:
            for table in sorted_tables[1:]:
                relationships = registry.join_relationships(base_table, table)
                join_from = registry.get_model(base_table)
                for relationship in relationships:
                    referenced_model = registry.get_model(relationship.model_ref)

                    if relationship.model_ref in already_joined_tables:
                        continue

                    if relationship.via:
                        query = query.join(
                            relationship.via,
                            on=f"{join_from.table}.{join_from.primary_key} = {relationship.via}.{relationship.self_key_column}",
                            join_type="inner",
                        )
                        query = query.join(
                            referenced_model.table,
                            on=f"{relationship.via}.{relationship.foreign_key_column} = {referenced_model.table}.{referenced_model.primary_key}",
                            join_type="inner",
                        )
                    else:
                        primary_key = referenced_model.primary_key
                        query = query.join(
                            referenced_model.table,
                            on=f"{join_from.table}.{relationship.foreign_key_column} = {referenced_model.table}.{primary_key}",
                            join_type="inner",
                        )

                    join_from = referenced_model
                    already_joined_tables.add(relationship.model_ref)
        query = query.group_by(*select_columns)
        return query


class ParameterizedSemanticQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_vars: t.List[str] = Field(default_factory=lambda: [])
    description: str = ""
    columns: t.List[str | exp.Column | t.Callable[..., str | exp.Column]] = Field(
        default_factory=lambda: []
    )
    filters: t.List[str | exp.Expression | t.Callable[..., str | exp.Expression]] = (
        Field(default_factory=lambda: [])
    )

    generators: t.Dict[str, t.List[t.Any]] = Field(default_factory=lambda: {})

    def __call__(
        self, inputs: t.Optional[t.Dict[str, t.List[t.Any]]]
    ) -> t.Sequence[SemanticQuery]:
        # using the inputs calculate the actual columns
        # Convert query into it's generated queries

        if not inputs:
            return [
                SemanticQuery(
                    columns=self.process_columns({}),
                    filters=self.process_filters({}),
                )
            ]
        permutations = reduce(
            lambda x, y: x * y, map(lambda x: len(x), inputs.values()), 1
        )
        key_order = list(inputs.keys())

        count = 0
        generated: t.List[SemanticQuery] = []
        while count < permutations:
            key_indices = {k: 0 for k in key_order}
            key_index_calc = count
            for key in key_order:
                key_indices[key] = key_index_calc % len(inputs[key])
                key_index_calc = key_index_calc // len(inputs[key])
            inputs = {k: v[key_indices[k]] for k, v in inputs.items()}
            generated.append(
                SemanticQuery(
                    columns=self.process_columns(inputs),
                    filters=self.process_filters(inputs),
                )
            )
        return generated

    def process_filters(self, inputs: t.Dict[str, t.Any]) -> t.List[exp.Expression]:
        filters: t.List[exp.Expression] = []
        for filter in self.filters:
            if callable(filter):
                filter = filter(**inputs)
            if isinstance(filter, str):
                filter = parse_one(filter)
            filters.append(filter)
        return filters

    def process_columns(
        self, inputs: t.Dict[str, t.Any]
    ) -> t.List[exp.Column | t.List[exp.Column]]:
        columns: t.List[exp.Column | t.List[exp.Column]] = []
        for column in self.columns:
            if callable(column):
                column = column(**inputs)

            if isinstance(column, str):
                if "->" in column:
                    column = list(map(lambda a: exp.to_column(a), column.split("->")))
                else:
                    column = exp.to_column(column)
                columns.append(column)
            elif isinstance(column, exp.Expression):
                if isinstance(column, exp.Column):
                    columns.append(column)
                else:
                    raise ValueError(f"Unsupported expression {column}")
        return columns


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
