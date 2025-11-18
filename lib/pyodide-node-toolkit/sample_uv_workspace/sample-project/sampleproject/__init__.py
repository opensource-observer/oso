from sqlglot import parse_one

def sample_func():
    parsed = parse_one("SELECT 1")
    return parsed.type
