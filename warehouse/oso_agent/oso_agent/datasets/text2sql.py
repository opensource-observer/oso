from typing import List

from ..types.datasets import Example, create_example

# proposing a p0, p1, p2 priority system, where: 
# p0 = critical, p1 = important, p2 = nice to have

TEXT2SQL_DATASET: List[Example] = [
    create_example(
        question="What's the total number of stars for each GitHub repo owned by opensource-observer?",
        answer="SELECT artifact_name AS repo_name, SUM(star_count) AS total_stars FROM repositories_v0 WHERE artifact_namespace = 'opensource-observer' GROUP BY 1",
        priority="P0",
        difficulty="easy",
        query_type=["filter", "aggregation"],
        query_domain=["github"]
    ),
    create_example(
        question="How many issues were opened and closed by the project Hypercerts during the year 2023?",
        answer="SELECT CASE WHEN m.metric_name = 'GITHUB_opened_issues_yearly' THEN 'Issues Opened' WHEN m.metric_name = 'GITHUB_closed_issues_yearly' THEN 'Issues Closed' END AS issue_status, SUM(COALESCE(ts.amount, 0)) AS total_count FROM timeseries_metrics_by_project_v0 ts JOIN projects_v1 p ON ts.project_id = p.project_id AND p.project_name = 'hypercerts' JOIN metrics_v0 m ON ts.metric_id = m.metric_id AND m.metric_name IN ('GITHUB_opened_issues_yearly','GITHUB_closed_issues_yearly') WHERE EXTRACT(YEAR FROM ts.sample_date) = 2023 GROUP BY 1",
        priority="P1",
        difficulty="medium",
        query_type=["filter", "aggregation", "join", "time-series", "derived metric"],
        query_domain=["github", "timeseries", "metrics"]
    ),
    create_example(
        question="How many projects are in one or more Optimism Retro Funding rounds?",
        answer="SELECT COUNT(DISTINCT pbc.project_id) AS num_projects FROM projects_by_collection_v1 pbc JOIN collections_v1 c ON pbc.collection_id = c.collection_id WHERE LOWER(c.display_name) LIKE '%retro%' OR LOWER(c.display_name) LIKE '%retrofunding%'",
        priority="P1",
        difficulty="medium",
        query_type=["join", "aggregation", "filter"],
        query_domain=["directory"]
    ),
    create_example(
        question="List all projects in the “ethereum-crypto-ecosystems” collection in alphabetical order",
        answer="SELECT DISTINCT p.project_name FROM projects_by_collection_v1 AS pc JOIN projects_v1 AS p ON pc.project_id = p.project_id WHERE collection_name = 'ethereum-crypto-ecosystems' ORDER BY p.project_name",
        priority="P0",
        difficulty="easy",
        query_type=["filter", "sort", "join"],
        query_domain=["directory"]
    ),
    create_example(
        question="List each project along with how many dependencies it's using.",
        answer="SELECT r.project_id, COUNT(DISTINCT d.dependency_artifact_id) AS dependency_count FROM int_code_dependencies AS d JOIN repositories_v0 AS r ON d.dependent_artifact_id = r.artifact_id GROUP BY r.project_id",
        priority="P0",
        difficulty="easy",
        query_type=["aggregation", "join"],
        query_domain=["github"]
    ),
    create_example(
        question="Show me the total gas used per day on Base over first month of 2024?",
        answer="SELECT sample_date, SUM(tm.amount) AS total_transactions FROM timeseries_metrics_by_project_v0 AS tm JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id WHERE m.metric_name LIKE 'BASE_gas_fees_daily' AND tm.sample_date BETWEEN DATE '2024-01-01' AND DATE '2024-01-31' GROUP BY sample_date ORDER BY sample_date",
        priority="P1",
        difficulty="medium",
        query_type=["time-series", "aggregation", "filter", "join", "sort"],
        query_domain=["blockchain", "timeseries", "metrics"]
    ),
    create_example(
        question="How much funding does each project get on average?",
        answer="SELECT SUM(e.amount) / COUNT(DISTINCT a.project_id) AS avg_funding FROM int_events__funding_awarded AS e JOIN artifacts_by_project_v1 AS a ON e.to_artifact_id = a.artifact_id",
        priority="P0",
        difficulty="easy",
        query_type=["aggregation", "join"],
        query_domain=["funding"]
    ),
    create_example(
        question="How many transactions did each project have on Cyber over the first quarter of 2025?",
        answer="SELECT tm.project_id, SUM(tm.amount) AS total_transactions FROM timeseries_metrics_by_project_v0 AS tm JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id WHERE m.metric_name LIKE 'CYBER_transactions_monthly' AND tm.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31' GROUP BY tm.project_id",
        priority="P0",
        difficulty="medium",
        query_type=["filter", "aggregation", "join", "time-series"],
        query_domain=["timeseries", "metrics"]
    ),
    create_example(
        question="Give me the daily commit count for the project \"Hypercerts\" over the first 2 weeks of 2024?",
        answer="SELECT tm.sample_date, SUM(tm.amount) AS daily_commit_count FROM timeseries_metrics_by_project_v0 AS tm JOIN projects_v1 AS p ON tm.project_id = p.project_id JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id WHERE p.project_name LIKE 'hypercerts' AND tm.sample_date BETWEEN DATE '2024-01-01' AND DATE '2024-01-14' AND m.metric_name LIKE '%commits_daily' GROUP BY tm.sample_date",
        priority="P1",
        difficulty="medium",
        query_type=["time-series", "aggregation", "filter", "join"],
        query_domain=["timeseries", "metrics"]
    ),
    create_example(
        question="List the names of GitHub repositories that are owned by opensource-observer.",
        answer="SELECT artifact_name AS repo_name FROM repositories_v0 WHERE artifact_namespace = 'opensource-observer'",
        priority="P0",
        difficulty="easy",
        query_type=["filter"],
        query_domain=["directory", "github"]
    ),
    create_example(
        question="Which chains does OSO have \"active contract\" metrics for? List them in alphabetical order.",
        answer="SELECT DISTINCT SPLIT_PART(m.metric_name, '_active_contracts_over_all_time', 1) AS chain FROM key_metrics_by_collection_v0 AS km JOIN metrics_v0 AS m ON km.metric_id = m.metric_id WHERE m.metric_name LIKE '%_active_contracts_over_all_time' ORDER BY chain",
        priority="P0",
        difficulty="medium",
        query_type=["filter", "sort", "join", "derived metric"],
        query_domain=["metrics"]
    ),
    create_example(
        question="Which project has increased DefiLlama TVL the most on any one chain (in absolute terms) in Q1 of 2025?",
        answer="WITH cte_defillama_tvl_metrics AS (SELECT metric_id, metric_name FROM metrics_v0 WHERE LOWER(metric_name) LIKE '%defillama%' AND LOWER(metric_name) LIKE '%tvl%'), cte_tvl_q1_2025 AS (SELECT ts.project_id, ts.metric_id, ts.sample_date, ts.amount FROM timeseries_metrics_by_project_v0 ts JOIN cte_defillama_tvl_metrics m ON ts.metric_id = m.metric_id WHERE ts.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31'), cte_tvl_start_end AS (SELECT DISTINCT project_id, metric_id, FIRST_VALUE(amount) OVER (PARTITION BY project_id, metric_id ORDER BY sample_date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS start_amount, LAST_VALUE(amount) OVER (PARTITION BY project_id, metric_id ORDER BY sample_date ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS end_amount FROM cte_tvl_q1_2025), cte_tvl_increase AS (SELECT project_id, metric_id, COALESCE(end_amount, 0) - COALESCE(start_amount, 0) AS absolute_tvl_increase FROM cte_tvl_start_end) SELECT p.display_name AS project_name, m.metric_name AS defillama_tvl_metric, ROUND(i.absolute_tvl_increase, 2) AS absolute_tvl_increase_q1_2025_usd FROM cte_tvl_increase i JOIN projects_v1 p ON i.project_id = p.project_id JOIN cte_defillama_tvl_metrics m ON i.metric_id = m.metric_id WHERE i.absolute_tvl_increase > 0 ORDER BY absolute_tvl_increase_q1_2025_usd DESC LIMIT 1",
        priority="P2",
        difficulty="hard",
        query_type=["derived metric", "subquery / cte", "filter", "join", "window function", "sort"],
        query_domain=["timeseries", "metrics"]
    ),
    create_example(
        question="Give me a list of all projects that have had at least 1000 transactions on INK, SONEIUM, and UNICHAIN. Sort them by total transactions across all three chains in descending order.",
        answer="WITH cte_relevant_metrics AS (SELECT metric_id, metric_name, CASE WHEN LOWER(metric_name) LIKE 'ink%contract_invocation%' THEN 'INK' WHEN LOWER(metric_name) LIKE 'soneium%contract_invocation%' THEN 'SONEIUM' WHEN LOWER(metric_name) LIKE 'unichain%contract_invocation%' THEN 'UNICHAIN' ELSE NULL END AS chain_name FROM metrics_v0 WHERE LOWER(metric_name) LIKE '%contract_invocation%' AND (LOWER(metric_name) LIKE 'ink%' OR LOWER(metric_name) LIKE 'soneium%' OR LOWER(metric_name) LIKE 'unichain%')), cte_project_chain_interactions AS (SELECT a.project_id, b.chain_name, SUM(a.amount) AS total_interactions FROM timeseries_metrics_by_project_v0 AS a JOIN cte_relevant_metrics AS b ON a.metric_id = b.metric_id WHERE b.chain_name IS NOT NULL GROUP BY a.project_id, b.chain_name), cte_project_summary AS (SELECT project_id, SUM(IF(chain_name = 'INK', total_interactions, 0)) AS ink_interactions, SUM(IF(chain_name = 'SONEIUM', total_interactions, 0)) AS soneium_interactions, SUM(IF(chain_name = 'UNICHAIN', total_interactions, 0)) AS unichain_interactions, SUM(total_interactions) AS total_interactions_all_chains FROM cte_project_chain_interactions GROUP BY project_id) SELECT DISTINCT p.display_name AS project_name, s.total_interactions_all_chains FROM cte_project_summary AS s JOIN projects_v1 AS p ON s.project_id = p.project_id WHERE s.ink_interactions >= 1000 AND s.soneium_interactions >= 1000 AND s.unichain_interactions >= 1000 ORDER BY s.total_interactions_all_chains DESC",
        priority="P2",
        difficulty="hard",
        query_type=["aggregation", "subquery / cte", "sort / limit", "join", "filter", "derived metric"],
        query_domain=["blockchain", "timeseries", "metrics"]
    ),
    create_example(
        question="How many projects are in the \"optimism\" collection?",
        answer="SELECT COUNT(DISTINCT project_id) AS project_count FROM projects_by_collection_v1 WHERE collection_name = 'optimism'",
        priority="P0",
        difficulty="easy",
        query_type=["filter", "aggregation"],
        query_domain=["directory"]
    ),
]