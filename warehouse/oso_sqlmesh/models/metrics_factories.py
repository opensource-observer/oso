import os

from dotenv import load_dotenv
from metrics_tools.definition import MetricMetadata
from metrics_tools.factory import MetricQueryDef, RollingConfig, timeseries_metrics

# Annoyingly sqlmesh doesn't load things in an expected order but we want to be
# able to override the start date for local testing and things
load_dotenv()

timeseries_metrics(
    start=os.environ.get("SQLMESH_TIMESERIES_METRICS_START", "2015-01-01"),
    catalog="metrics",
    model_prefix="timeseries",
    timeseries_sources=[
        "int_events_daily_to_artifact",
        "int_events_daily_to_artifact_with_lag",
        "int_issue_event_time_deltas",
        "int_first_of_event_from_artifact",
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
            ref="code/stars.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Stars",
                description="Metrics related to GitHub stars",
            ),
        ),
        "commits": MetricQueryDef(
            ref="code/commits.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Commits",
                description="Metrics related to GitHub commits",
            ),
        ),
        "comments": MetricQueryDef(
            ref="code/comments.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Comments",
                description="Metrics related to GitHub comments",
            ),
        ),
        "releases": MetricQueryDef(
            ref="code/releases.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Releases",
                description="Metrics related to GitHub releases",
            ),
        ),
        "forks": MetricQueryDef(
            ref="code/forks.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Forks",
                description="Metrics related to GitHub repository forks",
            ),
        ),
        "repositories": MetricQueryDef(
            ref="code/repositories.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Repositories",
                description="Metrics related to GitHub repositories",
            ),
        ),
        "active_contracts": MetricQueryDef(
            ref="blockchain/active_contracts.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Active Contracts",
                description="Metrics related to active blockchain contracts",
            ),
        ),
        "contributors": MetricQueryDef(
            ref="code/contributors.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Contributors",
                description="Metrics related to GitHub contributors",
            ),
        ),
        "active_developers": MetricQueryDef(
            ref="code/active_developers.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Active Developers",
                description="Metrics related to active GitHub developers",
            ),
        ),
        # This defines something with a rolling option that allows you to look back
        # to some arbitrary window. So you specify the window and specify the unit.
        # The unit and the window are used to pass in variables to the query. So it's
        # up to the query to actually query the correct window.
        # The resultant models are named as such
        # `metrics.timeseries_active_days_to_{entity_type}_over_{window}_{unit}`
        "developer_active_days": MetricQueryDef(
            ref="code/active_days.sql",
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
            ref="code/active_days.sql",
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
            ref="code/developer_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
            metadata=MetricMetadata(
                display_name="Developer Classifications",
                description="Metrics related to developer activity classifications",
            ),
        ),
        "contributor_classifications": MetricQueryDef(
            ref="code/contributor_activity_classification.sql",
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
            metadata=MetricMetadata(
                display_name="Contributor Classifications",
                description="Metrics related to contributor activity classifications",
            ),
        ),
        # Currently this query performs really poorly. We need to do some debugging on it
        # "user_retention_classifications": MetricQueryDef(
        #     ref="blockchain/user_retention_classification.sql",
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
            ref="code/change_in_developers.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@monthly",
                slots=32,
            ),
            metadata=MetricMetadata(
                display_name="Change in Developer Activity",
                description="Metrics related to change in developer activity",
            ),
        ),
        "opened_pull_requests": MetricQueryDef(
            ref="code/prs_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Opened Pull Requests",
                description="Metrics related to opened GitHub pull requests",
            ),
        ),
        "merged_pull_requests": MetricQueryDef(
            ref="code/prs_merged.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Merged Pull Requests",
                description="Metrics related to merged GitHub pull requests",
            ),
        ),
        "opened_issues": MetricQueryDef(
            ref="code/issues_opened.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Opened Issues",
                description="Metrics related to opened GitHub issues",
            ),
        ),
        "closed_issues": MetricQueryDef(
            ref="code/issues_closed.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Closed Issues",
                description="Metrics related to closed GitHub issues",
            ),
        ),
        "avg_prs_time_to_merge": MetricQueryDef(
            ref="code/prs_time_to_merge.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Average PR Time to Merge",
                description="Metrics related to average GitHub PR time to merge",
            ),
        ),
        "avg_time_to_first_response": MetricQueryDef(
            ref="code/time_to_first_response.sql",
            rolling=RollingConfig(
                windows=[90, 180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Average Time to First Response",
                description="Metrics related to average time to first response",
            ),
        ),
        "active_addresses_aggregation": MetricQueryDef(
            ref="blockchain/active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION_SUCCESS_DAILY_COUNT"],
            },
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=32,
            ),
            time_aggregations=["daily", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Active Addresses Aggregation",
                description="Metrics related to active blockchain addresses",
            ),
        ),
        "gas_fees": MetricQueryDef(
            ref="blockchain/gas_fees.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=16,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Gas Fees",
                description="Metrics related to blockchain gas fees",
            ),
        ),
        "transactions": MetricQueryDef(
            ref="blockchain/transactions.sql",
            rolling=RollingConfig(
                windows=[30, 90, 180],
                unit="day",
                cron="@daily",
                slots=32,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Transactions",
                description="Metrics related to blockchain transactions",
            ),
        ),
        "contributors_lifecycle": MetricQueryDef(
            ref="code/lifecycle.sql",
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
            metadata=MetricMetadata(
                display_name="Contributors Lifecycle",
                description="Metrics related to contributor lifecycle",
            ),
        ),
        "funding_received": MetricQueryDef(
            ref="funding/funding_received.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=8,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Funding Received",
                description="Metrics related to funding received",
            ),
        ),
        "dependencies": MetricQueryDef(
            ref="deps/dependencies.sql",
            rolling=RollingConfig(
                windows=[180],
                unit="day",
                cron="@daily",
                slots=16,
            ),
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Dependencies",
                description="Metrics related to dependencies",
            ),
        ),
    },
    default_dialect="clickhouse",
)
