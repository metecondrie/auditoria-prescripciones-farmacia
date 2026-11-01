"""Shared configuration; importing never connects to a database."""
import os
from sqlalchemy import create_engine


def engine_from_env():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("Definí DATABASE_URL; no se incluyen credenciales en el código.")
    return create_engine(url, hide_parameters=True)


def insert_rows(conn, table_name, rows):
    from sqlalchemy import MetaData, Table
    table = Table(table_name, MetaData(), autoload_with=conn)
    for offset in range(0, len(rows), 1000):
        conn.execute(table.insert(), rows[offset:offset + 1000])
