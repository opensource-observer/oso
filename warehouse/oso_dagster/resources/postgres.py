from contextlib import contextmanager

import psycopg2
from dagster import ConfigurableResource
from pydantic import Field


class PostgresResource(ConfigurableResource):
    """Resource for interacting with Supabase's PostgreSQL."""

    connection_url: str = Field(description="PostgreSQL connection URL.")

    @contextmanager
    def get_connection(self):
        """Provides a PostgreSQL connection."""
        conn = psycopg2.connect(self.connection_url)
        try:
            yield conn
        finally:
            conn.close()
