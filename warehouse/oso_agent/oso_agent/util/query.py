def sanitize_query_from_agent(query: str, input_dialect: str = "trino") -> str:
    """Sanitize a sql query from an agent response. This is to remove any
    unwanted characters or formatting that sometimes seem to appear in agent
    responses."""

    line_split = [ line.lower() for line in query.strip().split('\n')]
    if input_dialect.lower() in line_split:
        if line_split[0] == input_dialect.lower():
            query = "\n".join(line_split[1:])
    return query
