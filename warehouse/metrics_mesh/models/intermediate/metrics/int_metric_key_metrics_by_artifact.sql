MODEL (
  name metrics.int_metric_key_metrics_by_artifact,
  kind FULL,
  enabled false
);

@DEF(KIND, artifact);

WITH all_@{KIND}_metrics AS (
  @UNION(
    'ALL',
    "metrics"."key_issue_count_closed_to_@{KIND}_over_all_time",
    "metrics"."key_release_count_to_@{KIND}_over_all_time",
    "metrics"."key_first_commit_to_@{KIND}_over_all_time",
    "metrics"."key_pr_count_opened_to_@{KIND}_over_all_time",
    "metrics"."key_transaction_count_to_@{KIND}_over_all_time",
    "metrics"."key_active_developer_count_to_@{KIND}_over_all_time",
    "metrics"."key_last_commit_to_@{KIND}_over_all_time",
    "metrics"."key_time_to_first_response_to_@{KIND}_over_all_time",
    "metrics"."key_active_address_count_to_@{KIND}_over_all_time",
    "metrics"."key_dependencies_count_to_@{KIND}_over_all_time",
    "metrics"."key_gas_fees_to_@{KIND}_over_all_time",
    "metrics"."key_pr_count_merged_to_@{KIND}_over_all_time",
    "metrics"."key_pr_time_to_merge_to_@{KIND}_over_all_time",
    "metrics"."key_developer_count_to_@{KIND}_over_all_time",
    "metrics"."key_repository_count_to_@{KIND}_over_all_time",
    "metrics"."key_contributor_count_to_@{KIND}_over_all_time",
    "metrics"."key_funding_received_to_@{KIND}_over_all_time",
    "metrics"."key_star_count_to_@{KIND}_over_all_time",
    "metrics"."key_commit_count_to_@{KIND}_over_all_time",
    "metrics"."key_developer_active_day_count_to_@{KIND}_over_all_time",
    "metrics"."key_issue_count_opened_to_@{KIND}_over_all_time",
    "metrics"."key_active_contract_count_to_@{KIND}_over_all_time",
    "metrics"."key_comment_count_to_@{KIND}_over_all_time",
    "metrics"."key_contributor_active_day_count_to_@{KIND}_over_all_time",
    "metrics"."key_fork_count_to_@{KIND}_over_all_time"
  )
)

SELECT * FROM all_@{KIND}_metrics
