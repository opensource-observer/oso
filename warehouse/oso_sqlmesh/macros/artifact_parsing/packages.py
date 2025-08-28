from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


def _get_artifact_namespace_and_name(
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
) -> tuple[exp.Expression, exp.Expression]:
    """
    Extracts artifact namespace and name from package information.

    For MAVEN packages (group:artifact format), extracts namespace and name.
    For other packages, returns NULL for namespace and lowercase package name.

    Returns:
        Tuple of (artifact_namespace_expr, artifact_name_expr)
    """
    package_source_upper_expr = exp.Upper(this=package_source_expr)
    is_maven_expr = exp.EQ(
        this=package_source_upper_expr, expression=exp.Literal.string("MAVEN")
    )

    # Extract Maven group and artifact
    maven_namespace_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(":"),
            part_index=exp.Literal.number(1),
        )
    )
    maven_name_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(":"),
            part_index=exp.Literal.number(2),
        )
    )

    # Determine final namespace and name
    final_artifact_namespace_expr = (
        exp.Case().when(is_maven_expr, maven_namespace_expr).else_(exp.Null())
    )

    final_artifact_name_expr = (
        exp.Case()
        .when(is_maven_expr, maven_name_expr)
        .else_(exp.Lower(this=package_name_expr))
    )

    return final_artifact_namespace_expr, final_artifact_name_expr


def _construct_artifact_url(
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
    url_template_expr: exp.Expression,
) -> exp.Expression:
    """
    Constructs artifact URL using the provided template and package name.

    For MAVEN packages, converts group:artifact to group/artifact for URL.
    """
    package_source_upper_expr = exp.Upper(this=package_source_expr)
    is_maven_expr = exp.EQ(
        this=package_source_upper_expr, expression=exp.Literal.string("MAVEN")
    )

    # For Maven, convert group:artifact to group/artifact for URL
    package_name_for_url = (
        exp.Case()
        .when(
            is_maven_expr,
            exp.Anonymous(
                this="REPLACE",
                expressions=[
                    package_name_expr,
                    exp.Literal.string(":"),
                    exp.Literal.string("/"),
                ],
            ),
        )
        .else_(package_name_expr)
    )

    # Construct URL using template
    artifact_url_expr = exp.Coalesce(
        expressions=[
            exp.Anonymous(
                this="REPLACE",
                expressions=[
                    url_template_expr,
                    exp.Literal.string("{package_name}"),
                    package_name_for_url,
                ],
            ),
            exp.Null(),
        ]
    )

    return exp.Lower(this=artifact_url_expr)


@macro()
def parse_package_artifacts(
    evaluator: MacroEvaluator,
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
    url_template_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses package source and name to extract artifact details.

    Args:
        evaluator: The MacroEvaluator instance.
        package_source_expr: SQLGlot expression representing the canonical package source (e.g., 'NPM', 'PIP').
        package_name_expr: SQLGlot expression representing the package name.
                           For MAVEN, this is expected to be 'group:artifact'.
        url_template_expr: SQLGlot expression representing the URL template.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    # Extract namespace and name
    artifact_namespace_expr, artifact_name_expr = _get_artifact_namespace_and_name(
        package_source_expr, package_name_expr
    )

    # Construct URL
    artifact_url_expr = _construct_artifact_url(
        package_source_expr, package_name_expr, url_template_expr
    )

    # Build final select expression
    select_expr = exp.Select(
        expressions=[
            exp.Alias(
                this=package_source_expr, alias=exp.Identifier(this="artifact_source")
            ),
            exp.Alias(
                this=artifact_namespace_expr,
                alias=exp.Identifier(this="artifact_namespace"),
            ),
            exp.Alias(
                this=artifact_name_expr, alias=exp.Identifier(this="artifact_name")
            ),
            exp.Alias(
                this=artifact_url_expr, alias=exp.Identifier(this="artifact_url")
            ),
            exp.Alias(
                this=exp.Upper(this=exp.Literal.string("PACKAGE")),
                alias=exp.Identifier(this="artifact_type"),
            ),
        ]
    )

    return exp.Subquery(this=select_expr)
