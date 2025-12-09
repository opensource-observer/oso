import logging
import typing as t

from sqlglot import expressions as exp
from sqlglot.optimizer.normalize_identifiers import normalize_identifiers
from sqlmesh.core.macros import MacroEvaluator, macro
from sqlmesh.utils.errors import SQLMeshError

logger = logging.getLogger(__name__)


@macro()
def star_no_cast(
    evaluator: MacroEvaluator,
    relation: exp.Table,
    alias: exp.Column = t.cast(exp.Column, exp.column("")),
    exclude: t.Union[exp.Array, exp.Tuple] = exp.Tuple(expressions=[]),
    prefix: exp.Literal = exp.Literal.string(""),
    suffix: exp.Literal = exp.Literal.string(""),
    quote_identifiers: exp.Boolean = exp.true(),
):
    if alias and not isinstance(alias, (exp.Identifier, exp.Column)):
        raise SQLMeshError(f"Invalid alias '{alias}'. Expected an identifier.")
    if exclude and not isinstance(exclude, (exp.Array, exp.Tuple)):
        raise SQLMeshError(f"Invalid exclude '{exclude}'. Expected an array.")
    if prefix and not isinstance(prefix, exp.Literal):
        raise SQLMeshError(f"Invalid prefix '{prefix}'. Expected a literal.")
    if suffix and not isinstance(suffix, exp.Literal):
        raise SQLMeshError(f"Invalid suffix '{suffix}'. Expected a literal.")
    if not isinstance(quote_identifiers, exp.Boolean):
        raise SQLMeshError(
            f"Invalid quote_identifiers '{quote_identifiers}'. Expected a boolean."
        )

    excluded_names = {
        normalize_identifiers(excluded, dialect=evaluator.dialect).name
        for excluded in exclude.expressions
    }
    quoted = quote_identifiers.this
    table_identifier = alias.name or relation.name

    columns_to_types = {
        k: v
        for k, v in evaluator.columns_to_types(relation).items()
        if k not in excluded_names
    }
    return [
        exp.column(column, table=table_identifier, quoted=quoted).as_(
            f"{prefix.this}{column}{suffix.this}", quoted=quoted
        )
        for column, type_ in columns_to_types.items()
    ]


@macro()
def star_set(
    evaluator: MacroEvaluator,
    source: exp.Table,
    destination: exp.Table,
    source_alias: exp.Column = t.cast(exp.Column, exp.column("")),
    destination_alias: exp.Column = t.cast(exp.Column, exp.column("")),
    exclude: t.Union[exp.Array, exp.Tuple] = exp.Tuple(expressions=[]),
    prefix: exp.Literal = exp.Literal.string(""),
    suffix: exp.Literal = exp.Literal.string(""),
    quote_identifiers: exp.Boolean = exp.true(),
):
    if source_alias and not isinstance(source_alias, (exp.Identifier, exp.Column)):
        raise SQLMeshError(f"Invalid alias '{source_alias}'. Expected an identifier.")
    if destination_alias and not isinstance(
        destination_alias, (exp.Identifier, exp.Column)
    ):
        raise SQLMeshError(
            f"Invalid alias '{destination_alias}'. Expected an identifier."
        )
    if exclude and not isinstance(exclude, (exp.Array, exp.Tuple)):
        raise SQLMeshError(f"Invalid exclude '{exclude}'. Expected an array.")
    if prefix and not isinstance(prefix, exp.Literal):
        raise SQLMeshError(f"Invalid prefix '{prefix}'. Expected a literal.")
    if suffix and not isinstance(suffix, exp.Literal):
        raise SQLMeshError(f"Invalid suffix '{suffix}'. Expected a literal.")
    if not isinstance(quote_identifiers, exp.Boolean):
        raise SQLMeshError(
            f"Invalid quote_identifiers '{quote_identifiers}'. Expected a boolean."
        )

    excluded_names = {
        normalize_identifiers(excluded, dialect=evaluator.dialect).name
        for excluded in exclude.expressions
    }
    quoted = quote_identifiers.this
    source_identifier = source_alias.name or source.name
    destination_identifier = destination_alias.name or destination.name

    columns_to_types = {
        k: v
        for k, v in evaluator.columns_to_types(source).items()
        if k not in excluded_names
    }

    return [
        exp.EQ(
            this=exp.Column(
                this=exp.Identifier(
                    this=column,
                    quoted=quoted,
                ),
                table=destination_identifier,
            ),
            expression=exp.Column(
                this=exp.Identifier(
                    this=column,
                    quoted=quoted,
                ),
                table=source_identifier,
            ),
        )
        # exp.cast(
        #     exp.column(column, table=table_identifier, quoted=quoted),
        #     dtype,
        #     dialect=evaluator.dialect,
        # ).as_(f"{prefix.this}{column}{suffix.this}", quoted=quoted)
        for column, dtype in columns_to_types.items()
    ]
