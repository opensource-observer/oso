"""
This provides a _hopefully_ portable way to deal with data as it is
unnested by the UNNEST functions in trino and duckdb.

Given the following source columns (as pseudo code):

* `id` (int)
* `address` array<struct<street: string, city: string, state: string, zip:
string>>
* `phone_numbers` array<varchar>

In trino this is represented as the following:

```sql
CREATE TABLE source_table (
    id INT, address ARRAY(ROW(street VARCHAR, city VARCHAR, state VARCHAR, zip VARCHAR))
    phone_numbers ARRAY(VARCHAR)
)
```

In duckdb this is represented as the following:

```sql
CREATE TABLE source_table (
    id INT, address STRUCT(street TEXT, city TEXT, state TEXT, zip TEXT))
    phone_numbers ARRAY(TEXT)
)
```

Generally, these are approximately the same data structure from just
examination of the schema but Trino and DuckDB have different ways of
unnesting the structured data. The following are equivalent for
dealing with the array of structs that are unnested:

Trino:

```sql
SELECT
    address.street,
    address.city,
    address.state,
    address.zip
FROM source_table
CROSS JOIN UNNEST(address) AS address
```

DuckDB:

```sql
SELECT
    address.street,
    address.city,
    address.state,
    address.zip
FROM source_table
CROSS JOIN UNNEST(address) AS unnested(address)
```

So you can see that the reference to the unnested struct is different
between the two systems. This macro is meant to abstract that difference
away and provide a consistent way to reference the unnested struct.

In this next section the following are the equivalent queries for the
unnested arrays (the phone_numbers column):

Trino:

```sql
SELECT
    phone_number
FROM source_table
CROSS JOIN UNNEST(phone_numbers) AS unnested(phone_number)
```

DuckDB:

```sql
SELECT
    phone_number
FROM source_table
CROSS JOIN UNNEST(phone_numbers) AS unnested(phone_number)
```

These look the same but duckdb has a different way it can handle
this that trino cannot. Another way to write this in duckdb is like this:

```sql
SELECT
    UNNEST(phone_number) as phone_number
FROM source_table
CROSS JOIN UNNEST(phone_numbers) AS phone_number
```

Unfortunately, trino does not support this syntax. So these macros,
while a little verbose, should _always_ be used to reference the
unnested data.

So the following is how you would use these macros:

```sql
SELECT
    address.street as address_street,
    address.city as address_city,
    address.state as address_state,
    address.zip as address_zip,
    phone_number as phone_numbers
FROM source_table
CROSS JOIN UNNEST(address) AS @unnested_struct_ref(address)
CROSS JOIN UNNEST(phone_numbers) AS @unnested_array_ref(phone_number)
```

This will return the same data in both trino and duckdb.
"""

import uuid

from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


def unnested_reference_as_str(reference_name: exp.ExpOrStr) -> str:
    if isinstance(reference_name, str):
        return reference_name
    elif isinstance(reference_name, exp.Column):
        return reference_name.this
    else:
        raise ValueError("reference_name must be a string or column")


@macro()
def unnested_struct_ref(evaluator: MacroEvaluator, reference_name: exp.ExpOrStr):
    reference_name = unnested_reference_as_str(reference_name)

    if evaluator.runtime_stage in ["loading"]:
        return exp.to_identifier(reference_name)

    if evaluator.engine_adapter.dialect == "duckdb":
        # Add a random name for the table alias to prevent possible collisions
        random_name = uuid.uuid4().hex[0:8]
        return exp.TableAlias(
            this=exp.to_identifier(f"unnested_{random_name}"),
            columns=[exp.to_identifier(reference_name)],
        )
    elif evaluator.engine_adapter.dialect == "trino":
        return exp.to_identifier(reference_name)
    else:
        raise NotImplementedError(
            f"unnested_struct_ref not implemented for {evaluator.engine_adapter.dialect}"
        )


@macro()
def unnested_array_ref(evaluator: MacroEvaluator, reference_name: exp.ExpOrStr):
    reference_name = unnested_reference_as_str(reference_name)

    return exp.TableAlias(
        this=exp.to_identifier(f"unnested_alias_{reference_name}"),
        columns=[exp.to_identifier(reference_name)],
    )
