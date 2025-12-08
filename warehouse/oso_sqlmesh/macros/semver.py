from sqlglot import expressions as exp
from sqlmesh import macro


@macro()
def semver_extract(evaluator, column, part):
    part_str = part.name if part.is_string else part.name

    if part_str == "major":
        regex = r"^([0-9]+)"
    elif part_str == "minor":
        regex = r"^[0-9]+\.([0-9]+)"
    elif part_str == "patch":
        regex = r"^[0-9]+\.[0-9]+\.([0-9]+)"
    else:
        raise ValueError(f"Unknown semver part: {part_str}")

    return exp.Coalesce(
        this=exp.Try(
            this=exp.Cast(
                this=exp.RegexpExtract(
                    this=column,
                    expression=exp.Literal.string(regex),
                    group=exp.Literal.number(1),
                ),
                to=exp.DataType.build("integer"),
            )
        ),
        expressions=[exp.Literal.number(0)],
    )
