"""Semantic Annotations for SQLMesh"""

from sqlglot import exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro(metadata_only=True)
def provides(evaluator: MacroEvaluator, *args: exp.Column):
    """Semantic metadata to indicate that this model should be used as the
    canonical provider of data for the given columns.
    """
    print(args)

@macro(metadata_only=True)
def semantic_name(evaluator: MacroEvaluator, name: str):
    """Semantic metadata to indicate that this model is a semantic model.
    """
    print(name)