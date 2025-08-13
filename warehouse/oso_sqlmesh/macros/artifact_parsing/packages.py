from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def parse_package_artifacts(
    evaluator: MacroEvaluator,
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses package source and name to extract artifact details.

    Args:
        evaluator: The MacroEvaluator instance.
        package_source_expr: SQLGlot expression representing the package source (e.g., 'NPM', 'PYPI').
        package_name_expr: SQLGlot expression representing the package name.
                           For MAVEN, this is expected to be 'group:artifact'.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    artifact_source_upper_expr = exp.Upper(this=package_source_expr)
    
    is_maven_expr = exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('MAVEN'))
    
    maven_namespace_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(':'),
            part_index=exp.Literal.number(1)
        )
    )
    maven_name_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(':'),
            part_index=exp.Literal.number(2)
        )
    )
    
    final_artifact_namespace_expr = exp.Case().when(
        is_maven_expr, maven_namespace_expr
    ).else_(exp.Null())
    
    final_artifact_name_expr = exp.Case().when(
        is_maven_expr, maven_name_expr
    ).else_(exp.Lower(this=package_name_expr))

    # For URL construction, Maven needs name as group/artifact
    package_name_for_maven_url = exp.Anonymous(
        this="REPLACE",
        expressions=[
            package_name_expr,
            exp.Literal.string(':'),
            exp.Literal.string('/')
        ]
    )

    # Determine the correct name part for URL construction based on source
    # Most use package_name_expr directly, Maven uses the replaced version
    package_identifier_for_url = exp.Case().when(
        is_maven_expr, package_name_for_maven_url
    ).else_(package_name_expr)

    artifact_url_construction_expr = exp.Case() \
        .when(
            exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('NPM')),
            exp.Concat(expressions=[exp.Literal.string('https://www.npmjs.com/package/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('PYPI')),
            exp.Concat(expressions=[exp.Literal.string('https://pypi.org/project/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('CARGO')),
            exp.Concat(expressions=[exp.Literal.string('https://crates.io/crates/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('GO')),
            exp.Concat(expressions=[exp.Literal.string('https://pkg.go.dev/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            is_maven_expr, # Already checked artifact_source_upper_expr == 'MAVEN'
            exp.Concat(expressions=[exp.Literal.string('https://mvnrepository.com/artifact/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=artifact_source_upper_expr, expression=exp.Literal.string('NUGET')),
            exp.Concat(expressions=[exp.Literal.string('https://www.nuget.org/packages/'), package_identifier_for_url], safe=True)
        ) \
        .else_(exp.Null())
    
    final_artifact_url_expr = exp.Lower(this=artifact_url_construction_expr)
            
    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=artifact_source_upper_expr, alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=final_artifact_namespace_expr, alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=final_artifact_name_expr, alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=final_artifact_url_expr, alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('PACKAGE')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)


@macro()
def parse_sbom_artifacts(
    evaluator: MacroEvaluator,
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses package source and name to extract SBOM-related artifact details.
    Maps certain package sources to their SBOM equivalents (e.g., CARGO to RUST).

    Args:
        evaluator: The MacroEvaluator instance.
        package_source_expr: SQLGlot expression representing the package source (e.g., 'NPM', 'PYPI', 'CARGO').
        package_name_expr: SQLGlot expression representing the package name.
                           For MAVEN, this is expected to be 'group:artifact'.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    package_source_upper_expr = exp.Upper(this=package_source_expr)

    sbom_artifact_source_mapped_expr = exp.Case() \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('CARGO')),
            exp.Literal.string('RUST')
        ) \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('PYPI')),
            exp.Literal.string('PIP')
        ) \
        .else_(package_source_upper_expr)
    
    final_sbom_artifact_source_expr = sbom_artifact_source_mapped_expr # Already upper if not mapped, or literal string

    is_maven_expr = exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('MAVEN')) # Use original source for MAVEN check
    
    maven_namespace_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(':'),
            part_index=exp.Literal.number(1)
        )
    )
    maven_name_expr = exp.Lower(
        this=exp.SplitPart(
            this=package_name_expr,
            delimiter=exp.Literal.string(':'),
            part_index=exp.Literal.number(2)
        )
    )
    
    final_artifact_namespace_expr = exp.Case().when(
        is_maven_expr, maven_namespace_expr
    ).else_(exp.Null())
    
    final_artifact_name_expr = exp.Case().when(
        is_maven_expr, maven_name_expr
    ).else_(exp.Lower(this=package_name_expr))

    package_name_for_maven_url = exp.Anonymous(
        this="REPLACE",
        expressions=[
            package_name_expr,
            exp.Literal.string(':'),
            exp.Literal.string('/')
        ]
    )
    
    package_identifier_for_url = exp.Case().when(
        is_maven_expr, package_name_for_maven_url # Use original source for MAVEN check
    ).else_(package_name_expr)

    artifact_url_construction_expr = exp.Case() \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('NPM')),
            exp.Concat(expressions=[exp.Literal.string('https://www.npmjs.com/package/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('PYPI')),
            exp.Concat(expressions=[exp.Literal.string('https://pypi.org/project/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('CARGO')),
            exp.Concat(expressions=[exp.Literal.string('https://crates.io/crates/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('GO')),
            exp.Concat(expressions=[exp.Literal.string('https://pkg.go.dev/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            is_maven_expr, # Use original source for MAVEN check
            exp.Concat(expressions=[exp.Literal.string('https://mvnrepository.com/artifact/'), package_identifier_for_url], safe=True)
        ) \
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string('NUGET')),
            exp.Concat(expressions=[exp.Literal.string('https://www.nuget.org/packages/'), package_identifier_for_url], safe=True)
        ) \
        .else_(exp.Null())

    final_artifact_url_expr = exp.Lower(this=artifact_url_construction_expr)
            
    select_expr = exp.Select(
        expressions=[
            exp.Alias(this=final_sbom_artifact_source_expr, alias=exp.Identifier(this="artifact_source")),
            exp.Alias(this=final_artifact_namespace_expr, alias=exp.Identifier(this="artifact_namespace")),
            exp.Alias(this=final_artifact_name_expr, alias=exp.Identifier(this="artifact_name")),
            exp.Alias(this=final_artifact_url_expr, alias=exp.Identifier(this="artifact_url")),
            exp.Alias(this=exp.Upper(this=exp.Literal.string('PACKAGE')), alias=exp.Identifier(this="artifact_type")),
        ]
    )
    return exp.Subquery(this=select_expr)
