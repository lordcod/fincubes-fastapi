from typing import Any, Optional
from sqlalchemy import CTE, Table
from sqlalchemy.dialects import postgresql


def label_columns(table_or_cte: Table | CTE, prefix: str, include: Optional[set[str]] = None, exclude: Optional[set[str]] = None):
    columns = []
    for col in table_or_cte.c:
        if include and col.name not in include:
            continue
        if exclude and col.name in exclude:
            continue
        columns.append(col.label(f"{prefix}_{col.name}"))
    return columns


def prepare_columns(base_model, fields: dict[str, Any], prefix: str):
    filtered = {}
    prefix_with_underscore = f'{prefix}_'
    for name, value in fields.items():
        if name.startswith(prefix_with_underscore):
            trimmed = name[len(prefix_with_underscore):]
            filtered[trimmed] = value
    return base_model(**filtered)


def compile_query_with_dollar_params(query):
    compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={
                             "literal_binds": False})
    sql = str(compiled)
    params = compiled.params
    param_map = {name: f"${i+1}" for i, name in enumerate(params.keys())}

    for name, dollar in param_map.items():
        sql = sql.replace(f"%({name})s", dollar)

    param_values = params.values()
    return sql, list(param_values)
