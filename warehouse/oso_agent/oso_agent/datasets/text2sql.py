from typing import List

from ..types.datasets import Example, create_example

TEXT2SQL_DATASET: List[Example] = [
    create_example(
        question="How many projects are in the 'optimism' collection?",
        answer="SELECT COUNT(DISTINCT pbc.project_id) AS num_projects FROM projects_by_collection_v1 AS pbc JOIN collections_v1 AS c ON pbc.collection_id = c.collection_id WHERE c.display_name LIKE 'optimism'",
        priority="medium",
        difficulty="easy",
        query_type=["aggregation", "filter"],
        query_domain=["directory"]
    ),
    create_example(
        question="How many issues were opened and closed by the project Hypercerts during the year 2023?",
        answer="WITH ProjectFilter AS (SELECT project_id FROM projects_v1 WHERE project_name IN ('hypercerts')), MetricFilter AS (SELECT metric_id, metric_name, CASE WHEN metric_name = 'GITHUB_opened_issues_yearly' THEN 'Issues Opened' WHEN metric_name = 'GITHUB_closed_issues_yearly' THEN 'Issues Closed' ELSE 'Other' END AS issue_status FROM metrics_v0 WHERE metric_name IN ('GITHUB_opened_issues_yearly', 'GITHUB_closed_issues_yearly')) SELECT mf.issue_status, SUM(COALESCE(ts.amount, 0)) AS total_count FROM timeseries_metrics_by_project_v0 AS ts INNER JOIN ProjectFilter AS pf ON ts.project_id = pf.project_id INNER JOIN MetricFilter AS mf ON ts.metric_id = mf.metric_id WHERE EXTRACT(YEAR FROM ts.sample_date) = 2023 GROUP BY mf.issue_status",
        priority="medium",
        difficulty="medium",
        query_type=["aggregation", "filter"],
        query_domain=["directory", "metrics"]
    ),
]