from ..factories.sql import sql_assets

# TODO... replace this with a reference to the secret suffix to use in google's
# secret manager
connection_string = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"


ecosystems = sql_assets("ecosystems", connection_string, [{"table": "fake_timeseries"}])
