from sqlglot import exp, parse_one


def sample_func():
    parsed = parse_one("SELECT 1")
    if not isinstance(parsed, exp.Select):
        raise ValueError("Parsed expression is not a Select")
    return "success"
