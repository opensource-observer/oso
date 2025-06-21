from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_social_handle_artifact(
    evaluator: MacroEvaluator,
    platform_literal_expr: exp.Expression,
    url_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses a social media URL (Farcaster, Twitter) to extract artifact details.

    Args:
        evaluator: The MacroEvaluator instance.
        platform_literal_expr: SQLGlot expression for the platform name (e.g., 'FARCASTER', 'TWITTER').
        url_expr: SQLGlot expression representing the social media URL column.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    # platform_literal_expr is expected to be an exp.Literal.string already

    artifact_name_expr = exp.Case().when(
        exp.And(
            this=exp.EQ(this=platform_literal_expr, expression=exp.Literal.string('FARCASTER')),
            expression=exp.Like(this=url_expr, expression=exp.Literal.string('https://warpcast.com/%'))
        ),
        exp.Substring(this=url_expr, start=exp.Literal.number(22))
    ).when(
        exp.And(
            this=exp.EQ(this=platform_literal_expr, expression=exp.Literal.string('TWITTER')),
            expression=exp.Like(this=url_expr, expression=exp.Literal.string('https://twitter.com/%'))
        ),
        exp.Substring(this=url_expr, start=exp.Literal.number(21))
    ).when(
        exp.And(
            this=exp.EQ(this=platform_literal_expr, expression=exp.Literal.string('TWITTER')),
            expression=exp.Like(this=url_expr, expression=exp.Literal.string('https://x.com/%'))
        ),
        exp.Substring(this=url_expr, start=exp.Literal.number(15))
    ).else_(
        url_expr # Default
    )

    # Convert to x.com format for Twitter artifacts, keep original URL for others
    artifact_url_expr = exp.Case().when(
        exp.EQ(this=platform_literal_expr, expression=exp.Literal.string('TWITTER')),
        exp.Concat(
            expressions=[
                exp.Literal.string('https://x.com/'),
                exp.Lower(this=artifact_name_expr)
            ],
            safe=True
        )
    ).else_(
        exp.Lower(this=url_expr)
    )

    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=exp.Upper(this=platform_literal_expr), alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=exp.Lower(this=exp.Literal.string('')), alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=exp.Lower(this=artifact_name_expr), alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=artifact_url_expr, alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('SOCIAL_HANDLE')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
