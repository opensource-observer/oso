import os
from . import joiner_transform
from metrics_tools.utils import assert_same_sql


CURR_DIR = os.path.dirname(__file__)
FIXTURES_DIR = os.path.abspath(os.path.join(CURR_DIR, "fixtures"))


def get_sql_fixture(sql_path: str) -> str:
    return open(os.path.join(FIXTURES_DIR, sql_path), "r").read()


def test_factory():
    input = get_sql_fixture("basic/input.sql")
    artifact = joiner_transform(input, "artifact", ["events_daily_to_artifact"])
    assert artifact is not None
    assert len(artifact) == 1
    assert_same_sql(artifact[0], get_sql_fixture("basic/expected_artifact.sql"))

    project = joiner_transform(input, "project", ["events_daily_to_artifact"])
    assert project is not None
    assert len(project) == 1
    assert_same_sql(project[0], get_sql_fixture("basic/expected_project.sql"))
