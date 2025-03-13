import typing as t

import pytest
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.macros import MacroEvaluator, MacroRegistry

from .intermediate import run_intermediate_macro_evaluator, run_macro_evaluator
from .models.tools import create_unregistered_macro


@pytest.fixture
def macro_fixtures():
    def concat_macro(evaluator: MacroEvaluator, *args):
        return exp.Concat(
            expressions=args,
            safe=False,
            coalesce=False,
        )

    def get_state(evaluator: MacroEvaluator, key: str | exp.Expression):
        if isinstance(key, exp.Literal):
            key = key.this
        return exp.Literal(this=evaluator.locals["$$test_state"][key], is_string=True)

    registry = create_unregistered_macro(concat_macro)
    registry.update(create_unregistered_macro(get_state))
    return registry


@pytest.mark.parametrize(
    "input,expected,variables",
    [
        (
            "select @concat_macro('a', 'b', 'c') from test",
            "select CONCAT('a', 'b', 'c') from test",
            {},
        ),
        (
            "select @unknown_macro('a', 'b', 'c') from test",
            "select @unknown_macro('a', 'b', 'c') from test",
            {},
        ),
        (
            "select @concat_macro(@var1, 'b', 'c') from test",
            "select CONCAT('alpha', 'b', 'c') from test",
            {"var1": "alpha"},
        ),
        (
            "select @unknown_macro(@var1, 'b', 'c') from test",
            "select @unknown_macro('alpha', 'b', 'c') from test",
            {"var1": "alpha"},
        ),
        (
            "select @unknown_macro(@var1, 'b', @concat_macro(@somevar, @var2)) from test",
            "select @unknown_macro('alpha', 'b', CONCAT(@somevar, '2')) from test",
            {"var1": "alpha", "var2": "2"},
        ),
        (
            "select @get_state('foo'), @get_state('baz') from test",
            "select 'bar', 'bop' from test",
            {"$$test_state": {"foo": "bar", "baz": "bop"}},
        ),
    ],
)
def test_intermediate_macro_evaluator(
    macro_fixtures: MacroRegistry,
    input: str,
    expected: str,
    variables: t.Dict[str, t.Any],
):
    evaluated = run_intermediate_macro_evaluator(
        input, macro_fixtures, variables=variables
    )
    assert evaluated is not None
    assert len(evaluated) == 1
    assert qualify(evaluated[0]) == qualify(parse_one(expected))


@pytest.mark.parametrize(
    "input,expected,variables",
    [
        (
            "select @concat_macro('a', 'b', 'c') from test",
            "select CONCAT('a', 'b', 'c') from test",
            {},
        ),
        (
            "select @concat_macro('a', 'b', 'c') from test @WHERE(FALSE) 1 > 2",
            "select CONCAT('a', 'b', 'c') from test",
            {},
        ),
    ],
)
def test_macro_evaluator(
    macro_fixtures: MacroRegistry,
    input: str,
    expected: str,
    variables: t.Dict[str, t.Any],
):
    evaluated = run_macro_evaluator(input, macro_fixtures, variables=variables)
    assert evaluated is not None
    assert len(evaluated) == 1
    assert qualify(evaluated[0]) == qualify(parse_one(expected))


def test_macro_evaluator_fails():
    failed = False
    try:
        run_macro_evaluator("select @hi from table")
    except Exception:
        failed = True
    assert failed
