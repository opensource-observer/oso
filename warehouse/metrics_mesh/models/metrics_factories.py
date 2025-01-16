from metrics_tools.factory import MetricQueryDef, RollingConfig, timeseries_metrics

timeseries_metrics(
    start="2015-01-01",
    catalog="metrics",
    model_prefix="timeseries",
    timeseries_sources=[
        "events_daily_to_artifact",
        "events_daily_to_artifact_with_lag",
        "issue_event_time_deltas",
        "first_of_event_from_artifact",
    ],
    metric_queries={
        # This will automatically generate star counts for the given roll up periods.
        # A time_aggregation is just a simple addition of the aggregation. So basically we
        # calculate the daily time_aggregation every day by getting the count of the day.
        # Then the weekly every week by getting the count of the week and
        # monthly by getting the count of the month.
        # Additionally this will also create this along the dimensions (entity_types) of
        # project/collection so the resulting models will be named as follows
        # `metrics.timeseries_stars_to_{entity_type}_{time_aggregation}`
        "stars": MetricQueryDef(
            ref="stars.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "commits": MetricQueryDef(
            ref="commits.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "comments": MetricQueryDef(
            ref="comments.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "releases": MetricQueryDef(
            ref="releases.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "forks": MetricQueryDef(
            ref="forks.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "repositories": MetricQueryDef(
            ref="repositories.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "active_contracts": MetricQueryDef(
            ref="active_contracts.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "contributors": MetricQueryDef(
            ref="contributors.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        "active_developers": MetricQueryDef(
            ref="active_developers.sql",
            time_aggregations=["daily", "weekly", "monthly"],
        ),
        # This defines something with a rolling option that allows you to look back
        # to some arbitrary window. So you specify the window and specify the unit.
        # The unit and the window are used to pass in variables to the query. So it's
        # up to the query to actually query the correct window.
        # The resultant models are named as such
        # `metrics.timeseries_active_days_to_{entity_type}_over_{window}_{unit}`
        "developer_active_days": MetricQueryDef(
            ref="active_days.sql",
            vars={
                "activity_event_types": ["COMMIT_CODE"],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",  # This determines how often this is calculated
                slots=32,
            ),
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
        ),
        "contributor_active_days": MetricQueryDef(
            ref="active_days.sql",
            vars={
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",  # This determines how often this is calculated
                model_batch_size=90,
                slots=32,
            ),
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
        ),
        "developer_classifications": MetricQueryDef(
            ref="developer_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
        ),
        "contributor_classifications": MetricQueryDef(
            ref="contributor_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
        ),
        # Currently this query performs really poorly. We need to do some debugging on it
        # "user_retention_classifications": MetricQueryDef(
        #     ref="user_retention_classification.sql",
        #     vars={
        #         "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
        #     },
        #     rolling=RollingConfig(
        #         windows=[30, 90, 180],
        #         unit="day",
        #         cron="@daily",
        #     ),
        #     entity_types=["artifact", "project", "collection"],
        # ),
        "change_in_developer_activity": MetricQueryDef(
            ref="change_in_developers.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
        ),
        "commits_rolling": MetricQueryDef(
            ref="commits.sql",
            rolling=RollingConfig(
                windows=[10],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "opened_pull_requests": MetricQueryDef(
            ref="prs_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "merged_pull_requests": MetricQueryDef(
            ref="prs_merged.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "opened_issues": MetricQueryDef(
            ref="issues_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "closed_issues": MetricQueryDef(
            ref="issues_closed.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "avg_prs_time_to_merge": MetricQueryDef(
            ref="prs_time_to_merge.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "avg_time_to_first_response": MetricQueryDef(
            ref="time_to_first_response.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "active_addresses_aggregation": MetricQueryDef(
            ref="active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
            },
            time_aggregations=["daily", "monthly"],
        ),
        "active_addresses_rolling": MetricQueryDef(
            ref="active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=32,
            ),
        ),
        "gas_fees": MetricQueryDef(
            ref="gas_fees.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=16,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "transactions": MetricQueryDef(
            ref="transactions.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=32,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "contributors_lifecycle": MetricQueryDef(
            ref="lifecycle.sql",
            vars={
                "activity_event_types": [
                    "COMMIT_CODE",
                    "ISSUE_OPENED",
                    "PULL_REQUEST_OPENED",
                    "PULL_REQUEST_MERGED",
                ],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "funding_received": MetricQueryDef(
            ref="funding_received.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "dependencies": MetricQueryDef(
            ref="dependencies.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=16,
            ),
            entity_types=["artifact", "project", "collection"],
        ),
        "key_active_address_count": MetricQueryDef(
            ref="key_active_address_count.sql",
            entity_types=["artifact", "project", "collection"],
        ),
        "key_active_contract_count": MetricQueryDef(
            ref="key_active_contract_count.sql",
            entity_types=["artifact", "project", "collection"],
        ),
        "key_active_developer_count": MetricQueryDef(
            ref="key_active_developer_count.sql",
            entity_types=["artifact", "project", "collection"],
        ),
        "key_comment_count": MetricQueryDef(
            ref="key_comment_count.sql",
            entity_types=["artifact", "project", "collection"],
        ),
        "key_commit_count": MetricQueryDef(
            ref="key_commit_count.sql",
            entity_types=["artifact"],
        ),
        "key_contributor_active_day_count": MetricQueryDef(
            ref="key_contributor_active_day_count.sql",
            entity_types=["artifact"],
        ),
        "key_contributor_count": MetricQueryDef(
            ref="key_contributor_count.sql",
            entity_types=["artifact"],
        ),
        "key_dependencies_count": MetricQueryDef(
            ref="key_dependencies_count.sql",
            entity_types=["artifact"],
        ),
        "key_developer_active_day_count": MetricQueryDef(
            ref="key_developer_active_day_count.sql",
            entity_types=["artifact"],
        ),
        "key_developer_count": MetricQueryDef(
            ref="key_developer_count.sql",
            entity_types=["artifact"],
        ),
        "key_first_commit": MetricQueryDef(
            ref="key_first_commit.sql",
            entity_types=["artifact"],
        ),
        "key_fork_count": MetricQueryDef(
            ref="key_fork_count.sql",
            entity_types=["artifact"],
        ),
        "key_funding_received": MetricQueryDef(
            ref="key_funding_received.sql",
            entity_types=["artifact"],
        ),
        "key_gas_fees": MetricQueryDef(
            ref="key_gas_fees.sql",
            entity_types=["artifact"],
        ),
        "key_issue_count_closed": MetricQueryDef(
            ref="key_issue_count_closed.sql",
            entity_types=["artifact"],
        ),
        "key_issue_count_opened": MetricQueryDef(
            ref="key_issue_count_opened.sql",
            entity_types=["artifact"],
        ),
        "key_last_commit": MetricQueryDef(
            ref="key_last_commit.sql",
            entity_types=["artifact"],
        ),
        "key_pr_count_merged": MetricQueryDef(
            ref="key_pr_count_merged.sql",
            entity_types=["artifact"],
        ),
        "key_pr_count_opened": MetricQueryDef(
            ref="key_pr_count_opened.sql",
            entity_types=["artifact"],
        ),
        "key_pr_time_to_merge": MetricQueryDef(
            ref="key_pr_time_to_merge.sql",
            entity_types=["artifact"],
        ),
        "key_release_count": MetricQueryDef(
            ref="key_release_count.sql",
            entity_types=["artifact"],
        ),
        "key_repository_count": MetricQueryDef(
            ref="key_repository_count.sql",
            entity_types=["artifact"],
        ),
        "key_star_count": MetricQueryDef(
            ref="key_star_count.sql",
            entity_types=["artifact"],
        ),
        "key_time_to_first_response": MetricQueryDef(
            ref="key_time_to_first_response.sql",
            entity_types=["artifact"],
        ),
        "key_transaction_count": MetricQueryDef(
            ref="key_transaction_count.sql",
            entity_types=["artifact"],
        ),
    },
    default_dialect="clickhouse",
)
