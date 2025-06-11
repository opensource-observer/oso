from ..types.datasets import ExampleList, create_text2sql_example

TESTING_DATASET: ExampleList = ExampleList(examples=[
    create_text2sql_example(
        id="1",
        question="What's the total number of stars for each GitHub repo owned by opensource-observer?",
        answer_query="""
            SELECT 
                a.artifact_name AS repo_name, 
                km.amount AS total_stars 
            FROM oso.key_metrics_by_artifact_v0 AS km 
            JOIN oso.metrics_v0 AS m ON km.metric_id = m.metric_id 
            JOIN oso.artifacts_v1 AS a ON km.artifact_id = a.artifact_id 
            WHERE a.artifact_namespace = 'opensource-observer' 
            AND m.metric_name = 'GITHUB_stars_over_all_time'
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["repo_or_package_metrics"],
        real_user_question=False
    ),
    create_text2sql_example(
        id="4",
        question="List all projects in the “ethereum-crypto-ecosystems” collection in alphabetical order",
        answer_query="""
            SELECT DISTINCT 
                p.project_name 
            FROM oso.projects_by_collection_v1 AS pc 
            JOIN oso.projects_v1 AS p 
                ON pc.project_id = p.project_id 
            WHERE collection_name = 'ethereum-crypto-ecosystems' 
            ORDER BY p.project_name
        """,
        priority="P0",
        difficulty="easy",
        question_categories=["project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
        id="12",
        question="Which project has increased DefiLlama TVL the most on any one chain (in absolute terms) in Q1 of 2025?",
        answer_query="""
            WITH cte_defillama_tvl_metrics AS (
                SELECT 
                    metric_id, 
                    metric_name 
                FROM oso.metrics_v0 
                WHERE 
                    LOWER(metric_name) LIKE '%defillama%' 
                    AND LOWER(metric_name) LIKE '%tvl%'
            ),
            cte_tvl_q1_2025 AS (
                SELECT 
                    ts.project_id, 
                    ts.metric_id, 
                    ts.sample_date, 
                    ts.amount 
                FROM oso.timeseries_metrics_by_project_v0 ts 
                JOIN cte_defillama_tvl_metrics m 
                    ON ts.metric_id = m.metric_id 
                WHERE 
                    ts.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31'
            ),
            cte_tvl_start_end AS (
                SELECT DISTINCT 
                    project_id, 
                    metric_id, 
                    FIRST_VALUE(amount) OVER (
                        PARTITION BY project_id, metric_id 
                        ORDER BY sample_date ASC 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) AS start_amount,
                    LAST_VALUE(amount) OVER (
                        PARTITION BY project_id, metric_id 
                        ORDER BY sample_date ASC 
                        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                    ) AS end_amount 
                FROM cte_tvl_q1_2025
            ),
            cte_tvl_increase AS (
                SELECT 
                    project_id, 
                    metric_id, 
                    COALESCE(end_amount, 0) - COALESCE(start_amount, 0) AS absolute_tvl_increase 
                FROM cte_tvl_start_end
            )
            SELECT 
                p.display_name AS project_name, 
                m.metric_name AS defillama_tvl_metric, 
                ROUND(i.absolute_tvl_increase, 2) AS absolute_tvl_increase_q1_2025_usd 
            FROM cte_tvl_increase i 
            JOIN oso.projects_v1 p ON i.project_id = p.project_id 
            JOIN cte_defillama_tvl_metrics m ON i.metric_id = m.metric_id 
            WHERE i.absolute_tvl_increase > 0 
            ORDER BY absolute_tvl_increase_q1_2025_usd DESC 
            LIMIT 1
        """,
        priority="P2",
        difficulty="hard",
        question_categories=["blockchain_activity", "comparative_or_trend_analysis"],
        real_user_question=False
    )
])