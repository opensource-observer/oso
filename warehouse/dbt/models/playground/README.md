# Playground only models

These models are used simply to copy data from the main public dataset into the
playground. These file names are patterned such that they can be used by
`oso_source` to get the correct source in downstream models. As such, you
_SHOULD NOT_ use the `oso_source()` macro within models in this directory.

While this can be run as part of a `dbt run`, it is best to run these models
first when initializing a new dev area or playground.
