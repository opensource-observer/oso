from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


def _harmonize_package_source(package_source_expr: exp.Expression) -> exp.Expression:
    """
    Harmonizes package sources to standard artifact source names.

    Maps package sources to their canonical artifact source names for SBOM compatibility:
    - CARGO -> RUST (Rust packages)
    - PYPI -> PIP (Python packages)
    - RUBYGEMS -> GEM (Ruby gems)
    - GOLANG -> GO (Go modules)
    - GITHUBACTIONS -> GITHUB (GitHub Actions are GitHub-based)
    - Others remain unchanged

    Package sources handled:
    - APK, COMPOSER, DEB, GEM, GITHUB, GO, MAVEN, NPM, NUGET, PUB, PYPI, SWIFT
    """
    package_source_upper_expr = exp.Upper(this=package_source_expr)

    harmonized_source_expr = (
        exp.Case()
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("CARGO")
            ),
            exp.Literal.string("RUST"),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("PYPI")
            ),
            exp.Literal.string("PIP"),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr,
                expression=exp.Literal.string("RUBYGEMS"),
            ),
            exp.Literal.string("GEM"),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("GOLANG")
            ),
            exp.Literal.string("GO"),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr,
                expression=exp.Literal.string("GITHUBACTIONS"),
            ),
            exp.Literal.string("GITHUB"),
        )
        .else_(package_source_upper_expr)
    )

    return harmonized_source_expr


def _construct_artifact_url(
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
) -> exp.Expression:
    """
    Constructs artifact URLs based on package source and name.

    Generates appropriate URLs for different package sources:
    - NPM: https://www.npmjs.com/package/{package_name}
    - PYPI: https://pypi.org/project/{package_name}
    - CARGO: https://crates.io/crates/{package_name}
    - GO/GOLANG: https://pkg.go.dev/{package_name}
    - MAVEN: https://mvnrepository.com/artifact/{group/artifact}
    - NUGET: https://www.nuget.org/packages/{package_name}
    - RUBYGEMS/GEM: https://rubygems.org/gems/{package_name}
    - GITHUB/GITHUBACTIONS: https://github.com/{package_name}
    - PUB: https://pub.dev/packages/{package_name}
    - SWIFT: https://github.com/{package_name} (Swift packages are typically on GitHub)
    - COMPOSER: https://packagist.org/packages/{package_name}
    - APK/DEB: NULL (system packages don't have standard web registries)
    - Others: NULL
    """
    package_source_upper_expr = exp.Upper(this=package_source_expr)
    is_maven_expr = exp.EQ(
        this=package_source_upper_expr, expression=exp.Literal.string("MAVEN")
    )

    # For Maven, convert group:artifact to group/artifact for URL
    package_name_for_maven_url = exp.Anonymous(
        this="REPLACE",
        expressions=[
            package_name_expr,
            exp.Literal.string(":"),
            exp.Literal.string("/"),
        ],
    )

    # Determine the correct package identifier for URL construction
    package_identifier_for_url = (
        exp.Case()
        .when(is_maven_expr, package_name_for_maven_url)
        .else_(package_name_expr)
    )

    # Construct URLs based on package source
    artifact_url_expr = (
        exp.Case()
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("NPM")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://www.npmjs.com/package/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("PYPI")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://pypi.org/project/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("CARGO")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://crates.io/crates/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(this=package_source_upper_expr, expression=exp.Literal.string("GO")),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://pkg.go.dev/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("GOLANG")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://pkg.go.dev/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            is_maven_expr,
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://mvnrepository.com/artifact/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("NUGET")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://www.nuget.org/packages/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr,
                expression=exp.Literal.string("RUBYGEMS"),
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://rubygems.org/gems/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("GEM")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://rubygems.org/gems/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("GITHUB")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://github.com/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr,
                expression=exp.Literal.string("GITHUBACTIONS"),
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://github.com/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("PUB")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://pub.dev/packages/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr, expression=exp.Literal.string("SWIFT")
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://github.com/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .when(
            exp.EQ(
                this=package_source_upper_expr,
                expression=exp.Literal.string("COMPOSER"),
            ),
            exp.Concat(
                expressions=[
                    exp.Literal.string("https://packagist.org/packages/"),
                    package_identifier_for_url,
                ],
                safe=True,
            ),
        )
        .else_(exp.Null())
    )

    return exp.Lower(this=artifact_url_expr)


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


@macro()
def parse_depsdev_artifacts(
    evaluator: MacroEvaluator,
    package_source_expr: exp.Expression,
    package_name_expr: exp.Expression,
) -> exp.Expression:
    """
    Parses package source and name to extract deps.dev artifact details.

    Uses original package sources without harmonization for deps.dev compatibility.

    Args:
        evaluator: The MacroEvaluator instance.
        package_source_expr: SQLGlot expression representing the package source (e.g., 'NPM', 'PYPI').
        package_name_expr: SQLGlot expression representing the package name.
                           For MAVEN, this is expected to be 'group:artifact'.

    Returns:
        A SQLGlot Subquery expression containing a SELECT statement with columns:
        artifact_source, artifact_namespace, artifact_name, artifact_url, artifact_type
    """
    # Use original package source (no harmonization for deps.dev)
    artifact_source_expr = exp.Upper(this=package_source_expr)

    # Extract namespace and name
    artifact_namespace_expr, artifact_name_expr = _get_artifact_namespace_and_name(
        package_source_expr, package_name_expr
    )

    # Construct URL
    artifact_url_expr = _construct_artifact_url(package_source_expr, package_name_expr)

    # Build final select expression
    select_expr = exp.Select(
        expressions=[
            exp.Alias(
                this=artifact_source_expr, alias=exp.Identifier(this="artifact_source")
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
    # Harmonize package source for SBOM compatibility
    artifact_source_expr = _harmonize_package_source(package_source_expr)

    # Extract namespace and name
    artifact_namespace_expr, artifact_name_expr = _get_artifact_namespace_and_name(
        package_source_expr, package_name_expr
    )

    # Construct URL (use original source for URL construction)
    artifact_url_expr = _construct_artifact_url(package_source_expr, package_name_expr)

    # Build final select expression
    select_expr = exp.Select(
        expressions=[
            exp.Alias(
                this=artifact_source_expr, alias=exp.Identifier(this="artifact_source")
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
