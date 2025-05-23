from .valid_sql import ValidSqlEvaluator


def test_valid_sql():
    eval = ValidSqlEvaluator()
    assert eval.evaluate(response="SELECT * FROM table WHERE id = 1").passing
    assert eval.evaluate(response="SELECT * FROM table WHERE id = 1;").passing
    assert eval.evaluate(response="SELECT FROM table WHERE id = 1;").passing
    assert not eval.evaluate(response="SEL FROM table WHERE id = 1;").passing