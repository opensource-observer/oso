"""
Fake data generators
"""

import random
import string
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine


def random_text(size: int = 20):
    return "".join(random.choices(string.ascii_lowercase, k=size))


def generate_sql_table_data(connection_string: str, fill_size: int = 100):
    engine = create_engine(connection_string)

    metadata = MetaData()

    fake_timeseries = Table(
        "fake_timeseries",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("time", DateTime, nullable=False),
        Column("text", String(120), nullable=False),
    )

    with engine.connect() as conn:
        metadata.create_all(conn)

        for i in range(fill_size):
            insert_stmt = fake_timeseries.insert().values(
                time=datetime.now(), text=random_text()
            )
            conn.execute(insert_stmt)
        conn.commit()
