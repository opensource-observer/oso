
from pyoso.client import Client


def marimo_db():
    """Sets up a database connection for marimo to use with pyoso."""

    # Relies on an internal class from marimo (would love if it wasn't internal)
    return Client().dbapi_connection()
