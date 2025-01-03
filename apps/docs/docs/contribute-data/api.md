---
title: Crawl an API
sidebar_position: 4
---

We expect one of the most common forms of data connection would be to connect
some public API to OSO. We have created tooling to make this as easy as possible.

This workflow relies on a toolset called [dlt](https://dlthub.com). Simply, the dlt
library provides a set of tools to make connecting data sources to a
warehouse (or any other destination) very simple. There is a bit of complexity
in configuring many of the aspects of dlt to write to the final destination so
we've provided some helper functions and factories for you to concentrate on
simply write a proper dlt source that crawls the api.

## `dlt` overview

Before you start writing your own API crawler, it's important to understand some
of the key concepts of DLT. We highly suggest that you read the [dlt
docs](https://dlthub.com/docs/intro) as they give a more thorough introduction.
The outline here is simply an overview to get you to a very basic level of
understanding.

### DLT Concepts

The main concepts we will care about from DLT are:

- [Resource][DltResource]
  - A resource should be thought of as the collection of data for a single
    table. The majority of the code that is needed to collect data from some
    data source would be located in this resource.
- [Source][DltSource]
  - A Source is a collection of resources. In something like postgres, you
    might think of this as a schema or a dataset in bigquery.
- [Destination](https://dlthub.com/docs/general-usage/destination)
  - While you shouldn't be creating your own destination when adding to OSO,
    this concept is as it sounds, it's the final place you'd like to have your
    collected source stored.
- [Pipeline](https://dlthub.com/docs/general-usage/pipeline)
  - The pipeline orchestrates the flow of data from the source to the
    destination. In general, our tools have abstracted this away as well. So
    you likely won't need to interact directly with it.

[DltResource]: https://dlthub.com/docs/general-usage/resource
[DltSource]: https://dlthub.com/docs/general-usage/source

### DLT and Dagster

Dagster has 1st party support for integrating dlt as an asset. However, the
provided tools still require quite a bit of boiler plate configuration. In
response to this, we have created a set of tooling in our `oso_dagster` library
that should remove the need to understand or even interact with the initial
boilerplate.

## Create DLT Dagster Assets

With the tooling in `oso_dagster`, writing a DLT asset for our dagster
deployment involves just writing a [DLT Resource][DltResource] and using
`oso_dagster`'s `dlt_factory` decorator to wire it together.

### Basic Example

The following is a simple example that uses an example derived from [dlt's
docs](https://dlthub.com/docs/general-usage/http/overview#explicitly-specifying-pagination-parameters)

```python
# This file should be in warehouse/oso_dagster/assets/name_of_asset_group.py
import dlt
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import JSONResponsePaginator
from pydantic import BaseModel

from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns

poke_client = RESTClient(                                 # (1)
    base_url="https://pokeapi.co/api/v2",
    paginator=JSONResponsePaginator(next_url_path="next"),
    data_selector="results",
)

class Pokemon(BaseModel):                                 # (2)
    name: str
    url: str


@dlt.resource(                                            # (3)
    name="pokemon",
    columns=pydantic_to_dlt_nullable_columns(Pokemon),
)
def get_pokemons():
    for page in poke_client.paginate(
        "/pokemon",
        params={
            "limit": 100,
        },
    ):
        for pokemon in page.results:
            yield pokemon

@dlt_factory()                                            # (4)
def pokemon():
    yield get_pokemons()
```

The example has quite a few parts so we've added numbered sections to assist in
explanation.

1. Here we initialize a global client for the [pokeapi](https://pokeapi.co) that
   uses DLT's provided `RESTClient`. The `RESTCLient` is a wrapper around the
   popular [`requests`](https://requests.readthedocs.io/en/latest/) library. For
   more details on this, see the [dlt docs on the
   subject](https://dlthub.com/docs/general-usage/http/rest-client).
2. A pydantic Model that is derived from the
   [`pydantic.BaseModel`](https://docs.pydantic.dev/latest/api/base_model/).
   This model is used to derive the schema for the data generated from a dlt
   resource. This will later be used when configuring the dlt resource in
   section `(3)`.
3. The [DltResource][DltResource]. This is where the majority of logic should go
   for crawling any API in question. As depicted here, the dlt resource is
   created by using the `@dlt.resource` decorator. While not strictly necessary
   to define a dlt resource, we require that you provide a schema in the
   argument `columns` that matches the objects you wish to store in the data
   warehouse. This is generated from the pydantic model in `(2)`. Additionally,
   we use a function `pydantic_to_dlt_nullable_columns` to ensure that all of
   the columns when written to the datawarehouse are nullable. This allows dlt
   to better automatically handle schema changes in the future. If you do not
   want to use nullable columns, you can discuss with us in a PR as to why that
   might be and we can offer alternative implementations.
4. The asset definition. This is the simplest form of asset that one can define
   using the `@dlt_factory` decorator. The expected return type of a function
   decorated by `@dlt_factory` is `Iterable[DltResource]`. In more complicated
   use cases as you will see in the next example, this can be used to wire any
   dependencies required by the resource function.

### Using Secrets with APIs

Often an API will need some form of authentication. In such a case, the
authentication secrets should not be committed into the repository. If we see
such a thing during a review we will request for changes.

The following example fictiously adds authenticaton to the previously used
pokemon API. To enable use of secrets, You will need to map the necessary
secrets as arguments into the source by using the `secret_ref_arg`. This special
function is used by OSO's dagster's infrastructure to resolve secrets properly
from the currently configured `oso_dagster.utils.SecretResolver`. It takes two
arguments `group_name` and `key`. These are used to find a secret.

```python
from request.auth import HTTPBasicAuth
import dlt
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import JSONResponsePaginator
from pydantic import BaseModel

from oso_dagster.factories import dlt_factory, pydantic_to_dlt_nullable_columns

class Pokemon(BaseModel):
    name: str
    url: str


@dlt.resource(
    name="pokemon",
    columns=pydantic_to_dlt_nullable_columns(Pokemon),
)
def get_pokemons(poke_client: RESTClient):                # (1)
    for page in poke_client.paginate(
        "/pokemon",
        params={
            "limit": 100,
        },
    ):
        for pokemon in page.results:
            yield pokemon

@dlt_factory()
def pokemon(
    poke_user: str = secret_ref_arg(group_name="pokemon", key="username"),
    poke_pass: str = secret_ref_arg(group_name="pokemon", key="password")
):
    auth = HTTPBasicAuth(poke_user, poke_pass)       # (2)
    client = RESTClient(
        base_url="https://pokeapi.co/api/v2",
        paginator=JSONResponsePaginator(next_url_path="next"),
        data_selector="results",
        auth=auth,
    )
    yield get_pokemons(client)                       # (3)
```

There are a few critical changes we've made in this example:

1. You will notice that the RESTClient is no longer a global variable in the
   module. The dlt resource here now requires it as an argument. This will allow
   us to ensure we configure the authentication for this client properly
2. Starting on this line and the immediately following line, the authentication
   of for the `RESTClient` is configured. The details may differ if you're not
   using a RESTClient instance but this provides an example for how to pass in
   the required secrets to instantiate the necessary client.
3. The dlt resource is yielded as usual but it is instead passed the
   `RESTClient` instance that has been configured with authentication
   credentials.
