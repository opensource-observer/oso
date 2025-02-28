import pytest

from .types import (
    QueryJobState,
    QueryJobStateUpdate,
    QueryJobStatus,
    QueryJobTaskStatus,
    QueryJobTaskUpdate,
    QueryJobUpdate,
)


@pytest.mark.parametrize(
    "description,updates,expected_status,expected_has_remaining_tasks,expected_exceptions_count",
    [
        (
            "should fail if job failed",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.FAILED,
                        has_remaining_tasks=False,
                        exception="failed",
                    )
                )
            ],
            QueryJobStatus.FAILED,
            False,
            1,
        ),
        (
            "should still be running if no failure",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.RUNNING,
                        has_remaining_tasks=True,
                    ),
                ),
                QueryJobUpdate.create_task_update(
                    QueryJobTaskUpdate(
                        status=QueryJobTaskStatus.SUCCEEDED,
                        task_id="task_id",
                    )
                ),
            ],
            QueryJobStatus.RUNNING,
            True,
            0,
        ),
        (
            "should fail if task failed and still has remaining tasks",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.RUNNING,
                        has_remaining_tasks=True,
                    ),
                ),
                QueryJobUpdate.create_task_update(
                    QueryJobTaskUpdate(
                        status=QueryJobTaskStatus.FAILED,
                        task_id="task_id",
                        exception="failed",
                    )
                ),
            ],
            QueryJobStatus.FAILED,
            True,
            1,
        ),
        (
            "should fail if task failed and job failed but no remaining tasks",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.RUNNING,
                        has_remaining_tasks=True,
                    ),
                ),
                QueryJobUpdate.create_task_update(
                    QueryJobTaskUpdate(
                        status=QueryJobTaskStatus.FAILED,
                        task_id="task_id",
                        exception="failed",
                    )
                ),
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.FAILED,
                        has_remaining_tasks=False,
                        exception="failed",
                    )
                ),
            ],
            QueryJobStatus.FAILED,
            False,
            2,
        ),
        (
            "should fail if task failed and job supposedly completed but no remaining tasks",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.RUNNING,
                        has_remaining_tasks=True,
                    ),
                ),
                QueryJobUpdate.create_task_update(
                    QueryJobTaskUpdate(
                        status=QueryJobTaskStatus.FAILED,
                        task_id="task_id",
                        exception="failed",
                    )
                ),
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.COMPLETED,
                        has_remaining_tasks=False,
                    )
                ),
            ],
            QueryJobStatus.FAILED,
            False,
            1,
        ),
        (
            "should fail if a task is cancelled",
            [
                QueryJobUpdate.create_job_update(
                    QueryJobStateUpdate(
                        status=QueryJobStatus.RUNNING,
                        has_remaining_tasks=True,
                    ),
                ),
                QueryJobUpdate.create_task_update(
                    QueryJobTaskUpdate(
                        status=QueryJobTaskStatus.CANCELLED,
                        task_id="task_id",
                    )
                ),
            ],
            QueryJobStatus.FAILED,
            True,
            0,
        ),
    ],
)
def test_query_job_state(
    description,
    updates,
    expected_status,
    expected_has_remaining_tasks,
    expected_exceptions_count,
):
    state = QueryJobState.start("job_id", 4)
    for update in updates:
        state.update(update)
    assert state.status == expected_status, description
    assert state.has_remaining_tasks == expected_has_remaining_tasks, description

    response = state.as_response()
    assert response.status == expected_status, description
    assert len(response.exceptions) == expected_exceptions_count, description
