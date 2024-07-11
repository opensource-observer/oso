from dagster import asset, op, job
from .. import constants

if constants.enable_tests:

    @asset(compute_kind="fake")
    def fake_failing_asset() -> None:
        raise Exception("This fake asset only ever fails")

    @op(tags={"kind": "fake"})
    def fake_failing_op() -> None:
        raise Exception("This fake op only ever fails")

    @job()
    def fake_failing_job():
        fake_failing_op()
