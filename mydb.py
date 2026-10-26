import os
import re

import pandas as pd
import sqlparse
from sqlalchemy import create_engine

# mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE

engine = create_engine(
    "mysql+pymysql://root:password@localhost:3306/analytics"
)

# Schemas that ship with MySQL itself — usually not relevant to end users
SYSTEM_SCHEMAS = {"information_schema", "mysql", "performance_schema", "sys"}

# Optional allow-list, e.g. ALLOWED_SCHEMAS=analytics,reporting in .env.
# If unset, every non-system schema the DB user can see is shown.
ALLOWED_SCHEMAS = os.getenv("ALLOWED_SCHEMAS")

# Statement types/keywords that must never reach execute_query, even hidden
# inside a CTE, a subquery, or stacked after a semicolon.
FORBIDDEN_KEYWORDS = {
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE",
    "CREATE", "REPLACE", "GRANT", "REVOKE", "RENAME", "MERGE",
    "CALL", "LOCK", "UNLOCK", "SET", "USE", "EXECUTE",
}


class NotAllowedQueryError(Exception):
    """Raised when a submitted query is not a single, read-only SELECT."""


def validate_readonly_query(query: str) -> None:
    """
    Raises NotAllowedQueryError if `query` is not exactly one read-only
    SELECT (or WITH ... SELECT) statement. Raises without touching the
    database, so this should run *before* execute_query ever sees the query.
    """
    if not query or not query.strip():
        raise NotAllowedQueryError("No query was provided.")

    # Reject stacked statements (e.g. "SELECT ...; DROP TABLE ...")
    statements = [s for s in sqlparse.parse(query) if s.token_first(skip_cm=True)]
    if len(statements) != 1:
        raise NotAllowedQueryError(
            "Only a single SELECT statement is allowed per request."
        )

    statement = statements[0]

    first_token = statement.token_first(skip_cm=True)
    first_keyword = first_token.value.upper() if first_token else ""

    if first_keyword not in ("SELECT", "WITH"):
        raise NotAllowedQueryError(
            f"'{first_keyword or 'this'}' isn't allowed — only SELECT queries can be run."
        )

    # Belt-and-suspenders: scan every token (catches DML smuggled into a
    # subquery, a CTE, or after a comment) for a forbidden keyword.
    normalized = " ".join(
        token.value.upper() for token in statement.flatten() if token.ttype is not None
    )
    for word in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{word}\b", normalized):
            raise NotAllowedQueryError(
                f"The query contains '{word}', which isn't allowed. "
                "Only SELECT queries are permitted."
            )


def execute_query(query):
    validate_readonly_query(query)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    return df

def get_all_schemas(include_system=False):
    """
    Returns a list of all schema (database) names. If ALLOWED_SCHEMAS is set
    in the environment, results are restricted to that comma-separated list
    (regardless of include_system) so unrelated databases on the same MySQL
    server never show up in the picker.
    """
    query = "SELECT schema_name FROM information_schema.schemata;"
    df = execute_query(query)

    schemas = df["SCHEMA_NAME"].tolist() if "SCHEMA_NAME" in df.columns else df.iloc[:, 0].tolist()

    if not include_system:
        schemas = [s for s in schemas if s.lower() not in SYSTEM_SCHEMAS]

    if ALLOWED_SCHEMAS:
        allowed = {s.strip() for s in ALLOWED_SCHEMAS.split(",") if s.strip()}
        schemas = [s for s in schemas if s in allowed]

    return schemas

def get_tables(schema_name):
    """
    Returns a list of table names within a given schema.
    """
    query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{schema_name}'
        ORDER BY table_name;
    """
    df = execute_query(query)
    tables = df["TABLE_NAME"].tolist() if "TABLE_NAME" in df.columns else df.iloc[:, 0].tolist()
    return tables

def get_all_schemas_and_tables(include_system=False):
    """
    Returns a dict mapping each schema name to its list of tables, e.g.
    {
        "analytics": ["orders", "products", "customers"],
        "reporting": ["daily_sales", ...]
    }
    """
    schemas = get_all_schemas(include_system=include_system)
    return {schema: get_tables(schema) for schema in schemas}

def get_schema(table_name, schema_name="analytics"):
    query =f'''
        SELECT
        table_name,
        column_name,
        column_type
        FROM information_schema.columns
        WHERE table_schema = '{schema_name}'
        AND table_name = '{table_name}'
        ORDER BY ordinal_position;

'''
    schema = execute_query(query)
    return schema

# result = execute_query("select * from orders limit 5")
# result = get_schema('orders')
# print(result)

# all_schemas = get_all_schemas()
# print(all_schemas)

# tables_in_analytics = get_tables('analytics')
# print(tables_in_analytics)

# everything = get_all_schemas_and_tables()
# print(everything)