---
title: Semantic Layer
sidebar_position: 1
---

:::info
This guide is for actually defining the semantic layer of the data warehouse. If
you're just looking to make queries you should see the guide
[here](../get-started/using-semantic-layer.md)
:::

## The semantic layer

The OSO semantic layer allows us to provide a detailed interface to the OSO data
model that encapsulates the contextual meaning of tables, columns or other
abstractions in the data warehouse. The hope is that this interface will allow
new users an easy way to interrogate the data while also providing for
convenience tools when creating new models for seasoned users.

## Anatomy of the semantic layer

The semantic layer provides an interface that takes a lot of inspiration from
the wonderful work at [cube.dev](https://cube.dev). Many of the same
abstractions are used to provide a similar vocabulary for those familiar with
that tool. These abstractions and components are as such:

- `Model`
  - A model is a given object abstraction in for a given data type in the OSO
    data warehouse. At this time, it is expected that there's a single
    canonical table to represent a given Model. Models, like any object can
    relate to each other. For instance, the OSO data model has the concept of
    an Artifact which is part of zero or more Projects, and Projects which are
    part of zero or more Collections. Each of those entities are related to
    their associated Models.
- `Dimension`
  - A dimension is a non-aggregated attribute of a model. This could be
    something like an Artifact name, a Project namespace, a Collection
    description, an Event type, or Event time.
- `Measure`
  - A measure is an aggregated attribute of a model that is usually used to summarize values related to a model. This could be something like, the count of Artfiacts or sum of the amount dimension of Events.
- `Relationship`
  - A relationship defines a relationship is a special attribute that defines
    the relationship between one model and another. In sql, this is modelled as
    some kind of foreign key.
- `Interface`
  - Much like an interface in an object oriented language, an interface is a generic interface that can be applied to a given model. This allows us to provide
- `Registry`
  - A registry is the directory of all the models and their relationships to
    each other. Without the registry it's impossible to create a valid sql
    query.

## Defining the semantic layer

The semantic layer definitions are all JSON serializable Python objects. These
all represent objects detailed in the [Anatomy of the Semantic
Layer](#anatomy-of-semantic-layer) section above. This section will walk through
the definition of the `artifact`, `project`, and `collection` models. We will
start with a very basic definition of the `artifact` model and expand it to
include more attributes and relationships.

### OSO artifacts, projects and collections

Before we get to defining a semantic layer for these three entities, we need to
understand the meaning these entities hold in the context of OSO. Inside the OSO
data warehouse, artifacts, projects, and collections are generic entities to
understand the events that occur in the universe of open source software. These
entities roughly map to certain classes of real world or digital entities.

- Artifact entities
  - An artifact is generally an real or digital object that we consider the
    smallest atom that can send or receive events. This could be an NPM
    package, a Github repository, an Optimism contract, an Ethereum address,
    or any other entity that can be interacted with that is generally
    indivisible.
- Project entities
  - A project is a collection of artifacts that are related to each other in a
    some way. Usually, this project relates to some real world phyiscal or
    logical grouping of entities in the real world. In general, but not
    always, a project "owns" a set of artifacts rather than simply being
    composed of them. Examples of a project include an organization, a
    company, a team or even a single person.
- Collection entities
  - A collection is an arbitrary grouping of projects. The relationship
    between collections and projects is not necessarily one of ownership. For
    instance, a collection could be a set of projects that are related to a
    specific topic, or perhaps they're a set of projects involved in the same
    event. A collection could also be a set of projects that simply relate to
    another project. We see collections as a flexible way to group related
    projects but each collection may have a different purpose.

### An `artifact` model with dimensions

The model is the core abstraction of the semantic layer. It represents an
object in the OSO data warehouse that corresponds to a specific table. This
model then has a set of attributes that are one of `Dimension`, `Measure`, or
`Relationship`. Defining a model is done by creating a `Model` object with the
appropriate attributes.

To start, let's define a very basic model for the `artifact` table. This
definition will be incomplete but it will give us a starting point to understand
how to define a model.

```python
from oso_semantic import Model, Dimension

artifact_model = Model(
    name="artifact",
    table="iceberg.oso.artifacts_v1",
    dimensions=[
        Dimension(
            name="id",
            description="Unique identifier for the artifact",
            column_name="artifact_id",
        ),
        Dimension(
            name="name",
            description="Name of the artifact",
            column_name="artifact_name",
        ),
        Dimension(
            name="namespace",
            description="Namespace of the artifact",
            column_name="artifact_namespace"
        ),
        Dimension(
            name="source",
            description="Source of the artifact",
            column_name="artifact_source"
        ),
        Dimension(
            name="url",
            description="URL of the artifact",
            column_name="artifact_url"
        ),
    ]
)
```

At its most basic, a model must have a `name`, a `table`, and one or more
attributes. Here we've defined some basic dimensions for the `artifact` model.
Let's query this model to see what it looks like when translated to SQL. For
this we must first register this model to a registry and then create a query
against it.

To create the registry:

```python
from oso_semantic import Registry

registry = Registry()
registry.register(artifact_model)
```

To query, we use the `select` method on the registry, which creates a
`QueryBuilder` object that allows us to build a query against the registered
models.

```python
from oso_semantic import QueryBuilder

query: QueryBuilder = registry.select(
    "artifacts.id",
    "artifacts.name"
)

print(query.sql(pretty=True)) # Pretty print the SQL query
```

When querying, the `select` method simply takes a list of attributes that we
want to query. These attributes are specified in the format
`<model_name>.<attribute_name>`. In this case, we are querying the `id` and
`name` attributes of the `artifact` model. In the final line, we call
`query.sql(pretty=True)` and print the generated sql query to the console. This
will output as follows:

:::note
The sql generated by the semantic layer will actually be a bit more
verbose. This example is simplified to show the basic structure of the query.
:::

```sql
SELECT
    artifact.artifact_id as artifact__id,
    artifact.artifact_name as artifact__name
FROM iceberg.oso.artifacts_v1 as artifact
GROUP BY 1, 2
```

From this query you will notice that the tool is translating dimension names to
actual columns names in the underlying table. The `artifact.artifact_id` is the
column name in the `iceberg.oso.artifacts_v1` table that corresponds to the `id`
dimension of the `artifact` model.

Dimensions can also be filtered on. Let's filter only for artifacts that are
from the `GITHUB` source. We can do this by adding a filter to the query:

```python
query_with_filter: QueryBuilder = registry.select(
    "artifact.id",
    "artifact.name",
).where(
    "artifact.source = 'GITHUB'"
)
print(query_with_filter.sql(pretty=True))
```

The `where` method allows us to add a filter to the query using sql expressions.
The expressions look very similar to standard sql but instead of columns being
referenced, we use the model's attributes for filtering. The output of this
query will look like this:

```sql
SELECT
    artifact.artifact_id as artifact__id,
    artifact.artifact_name as artifact__name
FROM iceberg.oso.artifacts_v1 as artifact
WHERE artifact.artifact_source = 'GITHUB'
GROUP BY 1, 2
```

### Adding measures to the `artifact` model

Dimensions are useful for querying specific attributes of a model, but usually
we also want to perform some kind of aggregation on the data. This is where
measures come in. Measures are attributes that represent some kind of
aggregation of the data in the model. For instance, we might want to know the
count of artifacts or the distinct count of artifacts.

Here's an updated definition of the `artifact` model that includes measures and
a more complete set of dimensions:

```python
from oso_semantic import Model, Dimension, Measure

artifact_model = Model(
    name="artifact",
    table="iceberg.oso.artifacts_v1",
    primary_key="artifact_id",
    dimensions=[
        Dimension(
            name="id",
            description="Unique identifier for the artifact",
            column_name="artifact_id",
        ),
        Dimension(
            name="name",
            description="Name of the artifact",
            column_name="artifact_name",
        ),
        Dimension(
            name="namespace",
            description="Namespace of the artifact",
            column_name="artifact_namespace"
        ),
        Dimension(
            name="source",
            description="Source of the artifact",
            column_name="artifact_source"
        ),
        Dimension(
            name="url",
            description="URL of the artifact",
            column_name="artifact_url"
        ),
    ],
    measures=[
        Measure(
            name="count",
            description="Count of artifacts",
            query="count(self.id)",
        )
    ],
)
```

Now we have a more complete model that also includes the measure count of
artifacts. You will notice, that unlike a dimension, a measure does not have a
`column_name` attribute. Instead, it has a `query` attribute that defines how
the measure is calculated. In this case, the `count` measure is defined as
`count(self.id)`. Measures may only reference attributes of models. Related
models can also be referenced (covered later) but to prevent any ambiguity, the
semantic layer provides a special `self` keyword that resolves to the current
model instance.

If we query this model again, we can see how the measures are included in the
SQL query:

```python
# Recreate the registry with the updated model
registry = Registry()
registry.register(artifact_model)

# Query the model with the measure.
# This query will select the count of artifacts in a given source
count_query: QueryBuilder = registry.select(
    "artifact.source",
    "artifact.count"
)

print(count_query.sql(pretty=True))
```

The output of this query will look like this:

```sql
SELECT
    artifact.artifact_source as artifact__source,
    count(artifact.artifact_id) as artifact__count
FROM iceberg.oso.artifacts_v1 as artifact
GROUP BY 1
```

Much like, dimensions, measures can also be filtered on. For instance, if we
wanted to only return artifact sources that have more than 100 artifacts, we
could do the following:

```python
count_query_with_filter: QueryBuilder = registry.select(
    "artifact.source",
    "artifact.count"
).where(
    "artifact.count > 100"
)
print(count_query_with_filter.sql(pretty=True))
```

The generated SQL query will look like this:

```sql
SELECT
    artifact.artifact_source as artifact__source,
    count(artifact.artifact_id) as artifact__count
FROM iceberg.oso.artifacts_v1 as artifact
GROUP BY 1
HAVING count(artifact.artifact_id) > 100
```

### Adding relationships to the `artifact` model

Relationships are used to define how models relate to each other. This allows
the semantic layer to provide automatic joins between models when querying. In
order for this to work, we need to define the relationships between models and
classify them as either `one_to_one`, `one_to_many` or `many_to_one`. Many to
many relationships are not explicitly modeled in the semantic layer but can be
represented by a join table that is defined as a model.

:::Note
One potentially unintuitive aspect of the semantic layer is that relationships
are defined in a single direction and this is strictly enforced by the model
registry. This allows us to treat the entire semantic layer as a directed
acyclic graph. References within a model can happen in any direction but we
force the definition to define a direction of the relationship. This is
currently a limitation of the semantic layer and could change in the future.
:::

Let's add a model to represent the project entity called `project` and add the
relationships between the `artifact` and `project` models. Despite roughly
having a constraint that an artifact may only belong to a single project, the
data model is flexible enough to allow an artifact to be related to many
projects. For this reason, we model the artifact and project relationship as a
many to many relationship. This means we will also model the join table as a
model in the semantic layer.

```python
from oso_semantic import Model, Dimension, Measure, Relationship

# Let's redefine the registry and include the models without using
# intermediate variables
registry = Registry()


registry.register(Model(
    name="projects",
    description="A project is a collection of artifacts",
    primary_key="project_id",
    dimensions=[
        Dimension(
            name="project_id",
            description="Unique identifier for the project",
            column_name="project_id",
        ),
        Dimension(
            name="project_name",
            description="Name of the project",
            column_name="project_name",
        ),
        Dimension(
            name="project_description",
            description="Description of the project",
            column_name="project_description",
        ),
    ],
))

register.register(Model(
    name="artifacts_by_project",
    table="iceberg.oso.artifacts_by_project_v1",
    primary_key="artifact_id",
    description="Join table between artifacts and projects",
    dimensions=[
        Dimension(
            name="artifact_id",
            description="Unique identifier for the artifact",
            column_name="artifact_id",
        ),
        Dimension(
            name="project_id",
            description="Unique identifier for the project",
            column_name="project_id",
        ),
    ],
    relationships=[
        Relationship(
            name="project",
            ref_model="project",
            type="many_to_one",
            source_foreign_key="project_id",
            ref_key="project_id",
        )
    ]
))

registry.register(Model(
    name="artifacts",
    table="iceberg.oso.artifacts_v1",
    primary_key="artifact_id",
    dimensions=[
        Dimension(
            name="artifact_id",
            description="Unique identifier for the artifact",
            column_name="artifact_id",
        ),
        Dimension(
            name="artifact_name",
            description="Name of the artifact",
            column_name="artifact_name",
        ),
        Dimension(
            name="artifact_namespace",
            description="Namespace of the artifact",
            column_name="artifact_namespace"
        ),
        Dimension(
            name="artifact_source",
            description="Source of the artifact",
            column_name="artifact_source"
        ),
        Dimension(
            name="artifact_url",
            description="URL of the artifact",
            column_name="artifact_url"
        ),
    ],
    measures=[
        Measure(
            name="count",
            description="Count of artifacts",
            query="count(self.id)",
        ),
    ],
    relationships=[
        Relationship(
            name="by_project",
            description="Relationship to the artifacts_by_project model",
            ref_model="artifacts_by_project",
            type="many_to_one",
            source_foreign_key="artifact_id",
            ref_key="artifact_id",
        )
    ]
))
```

In this we have now defined the relationships between the `artifacts` and the
`projects` by mapping how the reference in one model translates to the referenced
model. The relationships themselves are not defined using model objects
explicity but rather reference models by names. This allows a more flexible way
to define each of the models. Once you start querying the models, however, the
registry is treated as immutable and the relationships are validated to ensure
that the model and any relationships are valid and do not have cycles.

Now if we query for both `artifacts` model attributes and `projects` model
attributes, the semantic layer will automatically join the two models together:

```python
query = registry.select(
    "artifacts.name",
    "projects.name",
)
print(query.sql(pretty=True))
```

The output of this query will look like this:

```sql
SELECT
    artifacts_12345678.artifact_name as artifact__name,
    projects_12345678.project_name as project__name
FROM iceberg.oso.artifacts_v1 as artifacts_12345678
LEFT JOIN iceberg.oso.artifacts_by_project_v1 as artifacts_by_project_1b23c4d
    ON artifacts_12345678.artifact_id = artifacts_by_project_1b23c4d.artifact_id
LEFT JOIN iceberg.oso.projects_v1 as projects_12345678
    ON artifacts_by_project_1b23c4d.project_id = projects_12345678.project_id
GROUP BY 1, 2
```
