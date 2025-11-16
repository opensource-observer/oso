# query-rewriter

Small python library for sql query rewriting for queries to the OSO data
warehouse.

To allow for easy use in both pyodide and python there's an injectable table
resolver that allows for using a javascript provided function. This architecture
allows us to reuse this in other places if needed, but for now, we attempt to
keep this package only as a dependency for the sql route in the api.
