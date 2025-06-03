import os
import typing as t

from dotenv import load_dotenv
from metrics_tools.definition import MetricMetadata
from metrics_tools.factory import MetricQueryConfig, MetricQueryDef, timeseries_metrics
from metrics_tools.models import constants
from sqlglot import exp

# Annoyingly sqlmesh doesn't load things in an expected order but we want to be
# able to override the start date for local testing and things
load_dotenv()


TRANSLATE_TIME_AGGREGATION = {
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
    "quarterly": "quarter",
    "biannually": "biannual",
    "yearly": "year",
}


def no_gaps_audit_factory(config: MetricQueryConfig) -> tuple[str, dict] | None:
    if not config["incremental"]:
        return None

    time_aggregation = config["ref"].get("time_aggregation")
    if time_aggregation is None:
        return None

    options: t.Dict[str, t.Any] = {
        "no_gap_date_part": TRANSLATE_TIME_AGGREGATION[time_aggregation],
        "time_column": exp.to_column(
            "metrics_sample_date",
        ),
    }
    if time_aggregation in ["biannually", "weekly", "quarterly"]:
        # Hack for now, ignore these until we fix the audit
        return None

    if "funding" in config["table_name"]:
        # Hack for now, ignore these until we fix the audit
        return None
    
    if "releases" in config["table_name"]:
        return None
    
    if "data_category=blockchain" in config["additional_tags"]:
        options["ignore_before"] = constants.superchain_audit_start
        options["missing_rate_min_threshold"] = 0.95

    return (
        "no_gaps",
        options,
    )


timeseries_metrics(
    default_dialect="trino",
    start=os.environ.get("SQLMESH_TIMESERIES_METRICS_START", "2015-01-01"),
    schema="oso",
    model_prefix="timeseries",
    timeseries_sources=[
        "int_issue_event_time_deltas",
        "int_first_of_event_from_artifact__github",
        "int_events_daily__blockchain",
        "int_events_daily__blockchain_token_transfers",
        "int_events_daily__4337",
        "int_events_daily__defillama_tvl",
        "int_events_daily__github",
        "int_events_daily__github_with_lag",
        "int_events_daily__funding",
    ],
    audits=[
        ("has_at_least_n_rows", {"threshold": 0}),
    ],
    audit_factories=[no_gaps_audit_factory],
    metric_queries={
        # This will automatically generate star counts for the given roll up periods.
        # A time_aggregation is just a simple addition of the aggregation. So basically we
        # calculate the daily time_aggregation every day by getting the count of the day.
        # Then the weekly every week by getting the count of the week and
        # monthly by getting the count of the month.
        # Additionally this will also create this along the dimensions (entity_types) of
        # project/collection so the resulting models will be named as follows
        # `oso.timeseries_stars_to_{entity_type}_{time_aggregation}`
        "stars": MetricQueryDef(
            ref="code/stars.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Stars",
                description="Metrics related to GitHub stars",
            ),
            additional_tags=["data_category=code"],
        ),
        "commits": MetricQueryDef(
            ref="code/commits.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Commits",
                description="Metrics related to GitHub commits",
            ),
            additional_tags=["data_category=code"],
        ),
        "comments": MetricQueryDef(
            ref="code/comments.sql",
            time_aggregations=["daily", "weekly", "monthly"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Comments",
                description="Metrics related to GitHub comments",
            ),
            additional_tags=["data_category=code"],
        ),
        "releases": MetricQueryDef(
            ref="code/releases.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Releases",
                description="Metrics related to GitHub releases",
            ),
            additional_tags=["data_category=code"],
        ),
        "forks": MetricQueryDef(
            ref="code/forks.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Forks",
                description="Metrics related to GitHub repository forks",
            ),
            additional_tags=["data_category=code"],
        ),
        "repositories": MetricQueryDef(
            ref="code/repositories.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Repositories",
                description="Metrics related to GitHub repositories",
            ),
            additional_tags=["data_category=code"],
        ),
        "active_contracts": MetricQueryDef(
            ref="blockchain/active_contracts.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Active Contracts",
                description="Metrics related to active blockchain contracts",
            ),
            additional_tags=["data_category=blockchain"],
        ),
        "contributors": MetricQueryDef(
            ref="code/contributors.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Contributors",
                description="Metrics related to GitHub contributors",
            ),
            additional_tags=["data_category=code"],
        ),
        # This defines something with a rolling option that allows you to look back
        # to some arbitrary window. So you specify the window and specify the unit.
        # The unit and the window are used to pass in variables to the query. So it's
        # up to the query to actually query the correct window.
        # The resultant models are named as such
        # `oso.timeseries_active_days_to_{entity_type}_over_{window}_{unit}`
        "developer_active_days": MetricQueryDef(
            ref="code/active_days.sql",
            vars={
                "activity_event_types": ["COMMIT_CODE"],
            },
            time_aggregations=[
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
            additional_tags=["data_category=code"],
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
            time_aggregations=[
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            is_intermediate=True,
            additional_tags=["data_category=code"],
        ),
        "developer_classifications": MetricQueryDef(
            ref="code/developer_activity_classification.sql",
            vars={
                "full_time_ratio": 10 / 30,
            },
            time_aggregations=[
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            metadata=MetricMetadata(
                display_name="Developer Classifications",
                description="Metrics related to developer activity classifications",
            ),
            additional_tags=["data_category=code"],
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
            time_aggregations=[
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            metadata=MetricMetadata(
                display_name="Contributor Classifications",
                description="Metrics related to contributor activity classifications",
            ),
            additional_tags=["data_category=code"],
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
        # "change_in_developer_activity": MetricQueryDef(
        #     ref="code/change_in_developers.sql",
        #     time_aggregations=[
        #         "monthly",
        #         "quarterly",
        #         "biannually",
        #         "yearly",
        #     ],
        #     metadata=MetricMetadata(
        #         display_name="Change in Developer Activity",
        #         description="Metrics related to change in developer activity",
        #     ),
        #     additional_tags=["data_category=code"],
        # ),
        "opened_pull_requests": MetricQueryDef(
            ref="code/prs_opened.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Opened Pull Requests",
                description="Metrics related to opened GitHub pull requests",
            ),
            additional_tags=["data_category=code"],
        ),
        "merged_pull_requests": MetricQueryDef(
            ref="code/prs_merged.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Merged Pull Requests",
                description="Metrics related to merged GitHub pull requests",
            ),
            additional_tags=["data_category=code"],
        ),
        "opened_issues": MetricQueryDef(
            ref="code/issues_opened.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Opened Issues",
                description="Metrics related to opened GitHub issues",
            ),
            additional_tags=["data_category=code"],
        ),
        "closed_issues": MetricQueryDef(
            ref="code/issues_closed.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Closed Issues",
                description="Metrics related to closed GitHub issues",
            ),
            additional_tags=["data_category=code"],
        ),
        # "avg_prs_time_to_merge": MetricQueryDef(
        #     ref="code/prs_time_to_merge.sql",
        #     time_aggregations=[
        #         "quarterly",
        #         "biannually",
        #     ],
        #     entity_types=["artifact", "project", "collection"],
        #     over_all_time=True,
        #     metadata=MetricMetadata(
        #         display_name="Average PR Time to Merge",
        #         description="Metrics related to average GitHub PR time to merge",
        #     ),
        #     additional_tags=["data_category=code"],
        # ),
        # "avg_time_to_first_response": MetricQueryDef(
        #     ref="code/time_to_first_response.sql",
        #     time_aggregations=[
        #         "quarterly",
        #         "biannually",
        #     ],
        #     entity_types=["artifact", "project", "collection"],
        #     over_all_time=True,
        #     metadata=MetricMetadata(
        #         display_name="Average Time to First Response",
        #         description="Metrics related to average time to first response",
        #     ),
        #     additional_tags=["data_category=code"],
        # ),
        "active_addresses_aggregation": MetricQueryDef(
            ref="blockchain/active_addresses.sql",
            vars={
                "activity_event_types": ["CONTRACT_INVOCATION"],
            },
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Active Addresses Aggregation",
                description="Metrics related to active blockchain addresses",
            ),
            additional_tags=["data_category=blockchain"],
        ),
        "gas_fees": MetricQueryDef(
            ref="blockchain/gas_fees.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Gas Fees",
                description="Metrics related to blockchain gas fees",
            ),
            additional_tags=["data_category=blockchain"],
        ),
        "transactions": MetricQueryDef(
            ref="blockchain/transactions.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Transactions",
                description="Metrics related to blockchain transactions",
            ),
            additional_tags=["data_category=blockchain"],
        ),
        # "token_transfers": MetricQueryDef(
        #     ref="blockchain/token_transfers.sql",
        #     time_aggregations=[
        #         "daily",
        #         "weekly",
        #         "monthly",
        #         "quarterly",
        #         "biannually",
        #         "yearly",
        #     ],
        #     entity_types=["artifact", "project", "collection"],
        #     over_all_time=True,
        #     metadata=MetricMetadata(
        #         display_name="Token Transfers",
        #         description="Metrics related to volume of blockchain token transfers",
        #     ),
        #     additional_tags=["data_category=blockchain"],
        # ),
        "contract_invocations": MetricQueryDef(
            ref="blockchain/contract_invocations.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Contract Invocations",
                description="Metrics related to blockchain contract invocations",
            ),
            additional_tags=["data_category=blockchain"],
        ),
        "defillama_tvl": MetricQueryDef(
            ref="blockchain/defillama_tvl.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                # "quarterly",
                # "biannually",
                "yearly",
            ],
            incremental=False,
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Defillama TVL",
                description="Metrics related to Defillama TVL",
            ),
            additional_tags=["data_category=defillama"],
        ),
        # "contributors_lifecycle": MetricQueryDef(
        #     ref="code/lifecycle.sql",
        #     vars={
        #         "activity_event_types": [
        #             "COMMIT_CODE",
        #             "ISSUE_OPENED",
        #             "PULL_REQUEST_OPENED",
        #             "PULL_REQUEST_MERGED",
        #         ],
        #     },
        #     time_aggregations=["monthly", "quarterly", "biannually", "yearly"],
        #     entity_types=["artifact", "project", "collection"],
        #     metadata=MetricMetadata(
        #         display_name="Contributors Lifecycle",
        #         description="Metrics related to contributor lifecycle",
        #     ),
        #     additional_tags=["data_category=code"],
        # ),
        "funding_received": MetricQueryDef(
            ref="funding/funding_received.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                "quarterly",
                "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Funding Received",
                description="Metrics related to funding received",
            ),
            additional_tags=["data_category=funding"],
        ),
        "funding_awarded": MetricQueryDef(
            ref="funding/funding_awarded.sql",
            time_aggregations=[
                "daily",
                "weekly",
                "monthly",
                "quarterly",
                "biannually",
                "yearly",
            ],
            entity_types=["artifact", "project", "collection"],
            over_all_time=True,
            metadata=MetricMetadata(
                display_name="Funding Awarded",
                description="Metrics related to funding awarded",
            ),
            additional_tags=["data_category=funding"],
        ),
        # "dependencies": MetricQueryDef(
        #     ref="deps/dependencies.sql",
        #     time_aggregations=[
        #         "daily",
        #         "weekly",
        #         "monthly",
        #         "quarterly",
        #         "biannually",
        #         "yearly",
        #     ],
        #     entity_types=["artifact", "project", "collection"],
        #     over_all_time=True,
        #     metadata=MetricMetadata(
        #         display_name="Dependencies",
        #         description="Metrics related to dependencies",
        #     ),
        #     additional_tags=[
        #         "data_category=dependencies",
        #     ],
        # ),
    },
)
