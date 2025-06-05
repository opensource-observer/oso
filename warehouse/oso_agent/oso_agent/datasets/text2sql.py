from typing import List

from ..types.datasets import Example, create_text2sql_example

TEXT2SQL_DATASET: List[Example] = [
    create_text2sql_example(
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
        question="How many issues were opened and closed by the project Hypercerts during the year 2023?",
        answer_query="""
            SELECT 
                CASE 
                    WHEN m.metric_name = 'GITHUB_opened_issues_yearly' THEN 'Issues Opened' 
                    WHEN m.metric_name = 'GITHUB_closed_issues_yearly' THEN 'Issues Closed' 
                END AS issue_status, 
                SUM(COALESCE(ts.amount, 0)) AS total_count 
            FROM oso.timeseries_metrics_by_project_v0 ts 
            JOIN oso.projects_v1 p 
                ON ts.project_id = p.project_id 
                AND p.project_name = 'hypercerts' 
            JOIN oso.metrics_v0 m 
                ON ts.metric_id = m.metric_id 
                AND m.metric_name IN ('GITHUB_opened_issues_yearly','GITHUB_closed_issues_yearly') 
            WHERE EXTRACT(YEAR FROM ts.sample_date) = 2023 
            GROUP BY 1
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["pr_and_issue_tracking"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How many projects are in one or more Optimism Retro Funding rounds?",
        answer_query="""
            SELECT 
                COUNT(DISTINCT pbc.project_id) AS num_projects 
            FROM oso.projects_by_collection_v1 pbc 
            JOIN oso.collections_v1 c 
                ON pbc.collection_id = c.collection_id 
            WHERE 
                LOWER(c.display_name) LIKE '%retro%' 
                OR LOWER(c.display_name) LIKE '%retrofunding%'
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
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
        question="List each project along with how many dependencies it's using.",
        answer_query="""
            SELECT 
                r.project_id, 
                COUNT(DISTINCT d.dependency_artifact_id) AS dependency_count 
            FROM oso.int_code_dependencies AS d 
            JOIN oso.repositories_v0 AS r 
                ON d.dependent_artifact_id = r.artifact_id 
            GROUP BY r.project_id
        """,
        priority="P0",
        difficulty="easy",
        question_categories=["dependencies_and_software"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Show me the total gas used per day on Base over first month of 2024?",
        answer_query="""
            SELECT 
                sample_date, 
                SUM(tm.amount) AS total_transactions 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                m.metric_name LIKE 'BASE_gas_fees_daily' 
                AND tm.sample_date BETWEEN DATE '2024-01-01' AND DATE '2024-01-31' 
            GROUP BY sample_date 
            ORDER BY sample_date
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How much funding does each project get on average?",
        answer_query="""
            SELECT 
                SUM(e.amount) / COUNT(DISTINCT a.project_id) AS avg_funding 
            FROM oso.int_events__funding_awarded AS e 
            JOIN oso.artifacts_by_project_v1 AS a 
                ON e.to_artifact_id = a.artifact_id
        """,
        priority="P0",
        difficulty="easy",
        question_categories=["funding_and_grants"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How many transactions did each project have on Cyber over the first quarter of 2025?",
        answer_query="""
            SELECT 
                tm.project_id, 
                SUM(tm.amount) AS total_transactions 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                m.metric_name LIKE 'CYBER_transactions_monthly' 
                AND tm.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31' 
            GROUP BY tm.project_id
        """,
        priority="P0",
        difficulty="medium",
        question_categories=["blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Give me the daily commit count for the project \"Hypercerts\" over the first 2 weeks of 2024?",
        answer_query="""
            SELECT 
                tm.sample_date, 
                SUM(tm.amount) AS daily_commit_count 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.projects_v1 AS p 
                ON tm.project_id = p.project_id 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                p.project_name LIKE 'hypercerts' 
                AND tm.sample_date BETWEEN DATE '2024-01-01' AND DATE '2024-01-14' 
                AND m.metric_name LIKE '%commits_daily' 
            GROUP BY tm.sample_date
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["developer_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="List the names of GitHub repositories that are owned by opensource-observer.",
        answer_query="""
            SELECT DISTINCT 
                artifact_name AS repo_name 
            FROM oso.artifacts_by_project_v1 
            WHERE 
                artifact_namespace = 'opensource-observer' 
                AND artifact_source = 'GITHUB'
        """,
        priority="P0",
        difficulty="easy",
        question_categories=["repo_or_package_metrics"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which chains does OSO have \"active contract\" metrics for? List them in alphabetical order.",
        answer_query="""
            SELECT DISTINCT 
                SPLIT_PART(m.metric_name, '_active_contracts_over_all_time', 1) AS chain 
            FROM oso.key_metrics_by_collection_v0 AS km 
            JOIN oso.metrics_v0 AS m 
                ON km.metric_id = m.metric_id 
            WHERE 
                m.metric_name LIKE '%_active_contracts_over_all_time' 
            ORDER BY chain
        """,
        priority="P0",
        difficulty="medium",
        question_categories=["blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
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
    ),
    create_text2sql_example(
        question="Give me a list of all projects that have had at least 1000 transactions on INK, SONEIUM, and UNICHAIN. Sort them by total transactions across all three chains in descending order.",
        answer_query="""
            WITH cte_relevant_metrics AS (
                SELECT 
                    metric_id, 
                    metric_name, 
                    CASE 
                        WHEN LOWER(metric_name) LIKE 'ink%contract_invocation%' THEN 'INK' 
                        WHEN LOWER(metric_name) LIKE 'soneium%contract_invocation%' THEN 'SONEIUM' 
                        WHEN LOWER(metric_name) LIKE 'unichain%contract_invocation%' THEN 'UNICHAIN' 
                        ELSE NULL 
                    END AS chain_name 
                FROM oso.metrics_v0 
                WHERE 
                    LOWER(metric_name) LIKE '%contract_invocation%' 
                    AND (
                        LOWER(metric_name) LIKE 'ink%' 
                        OR LOWER(metric_name) LIKE 'soneium%' 
                        OR LOWER(metric_name) LIKE 'unichain%'
                    )
            ),
            cte_project_chain_interactions AS (
                SELECT 
                    a.project_id, 
                    b.chain_name, 
                    SUM(a.amount) AS total_interactions 
                FROM oso.timeseries_metrics_by_project_v0 AS a 
                JOIN cte_relevant_metrics AS b 
                    ON a.metric_id = b.metric_id 
                WHERE b.chain_name IS NOT NULL 
                GROUP BY a.project_id, b.chain_name
            ),
            cte_project_summary AS (
                SELECT 
                    project_id, 
                    SUM(IF(chain_name = 'INK', total_interactions, 0)) AS ink_interactions, 
                    SUM(IF(chain_name = 'SONEIUM', total_interactions, 0)) AS soneium_interactions, 
                    SUM(IF(chain_name = 'UNICHAIN', total_interactions, 0)) AS unichain_interactions, 
                    SUM(total_interactions) AS total_interactions_all_chains 
                FROM cte_project_chain_interactions 
                GROUP BY project_id
            )
            SELECT DISTINCT 
                p.display_name AS project_name, 
                s.total_interactions_all_chains 
            FROM cte_project_summary AS s 
            JOIN oso.projects_v1 AS p 
                ON s.project_id = p.project_id 
            WHERE 
                s.ink_interactions >= 1000 
                AND s.soneium_interactions >= 1000 
                AND s.unichain_interactions >= 1000 
            ORDER BY s.total_interactions_all_chains DESC
        """,
        priority="P2",
        difficulty="hard",
        question_categories=["blockchain_activity", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How many projects are in the \"optimism\" collection?",
        answer_query="""
            SELECT 
                COUNT(DISTINCT project_id) AS project_count 
            FROM oso.projects_by_collection_v1 
            WHERE collection_name = 'optimism'
        """,
        priority="P0",
        difficulty="easy",
        question_categories=["project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="What’s the pull-request merge rate (merged vs total) for project “zora” the first quarter this year?",
        answer_query="""
            SELECT 
                SUM(CASE WHEN m.metric_name LIKE '%_merged_pull_requests_monthly' THEN tm.amount END) / 
                SUM(CASE WHEN m.metric_name LIKE '%_opened_pull_requests_monthly' THEN tm.amount END) AS merge_rate 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.projects_v1 AS p 
                ON tm.project_id = p.project_id 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                LOWER(p.display_name) LIKE 'zora' 
                AND tm.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31'
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["pr_and_issue_tracking"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How many funding transactions did each project receive in Q1 2025? I want the projects with the most transactions shown first.",
        answer_query="""
            SELECT 
                tm.project_id, 
                COUNT(*) AS funding_transactions 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
                AND m.metric_name LIKE '%funding_awarded_quarterly' 
            WHERE 
                tm.sample_date BETWEEN DATE '2025-01-01' AND DATE '2025-03-31' 
            GROUP BY tm.project_id 
            ORDER BY funding_transactions DESC
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["funding_and_grants"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which projects have at least 100 GitHub stars and have received over $1M in funding?",
        answer_query="""
            SELECT 
                project_id 
            FROM oso.key_metrics_by_project_v0 AS km 
            JOIN oso.metrics_v0 AS m 
                ON km.metric_id = m.metric_id 
            GROUP BY project_id 
            HAVING 
                SUM(CASE WHEN m.metric_name = 'GITHUB_stars_over_all_time' THEN km.amount END) >= 100 
                AND SUM(CASE WHEN m.metric_name LIKE '%funding_awarded%' THEN km.amount END) > 1000000
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["funding_and_grants", "repo_or_package_metrics"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="What projects saw their TVL exceed $10 M on both Optimism and Arbitrum in Q4 2024?",
        answer_query="""
            SELECT 
                tm.project_id 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
                AND m.metric_name LIKE '%defillama_tvl_monthly' 
            WHERE 
                tm.sample_date BETWEEN DATE '2024-10-01' AND DATE '2024-12-31' 
            GROUP BY tm.project_id 
            HAVING 
                MAX(CASE WHEN m.metric_name LIKE 'OPTIMISM_%' THEN tm.amount ELSE 0 END) > 10000000 
                AND MAX(CASE WHEN m.metric_name LIKE 'ARBITRUM_ONE%' THEN tm.amount ELSE 0 END) > 10000000
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="How many full-time active developers were in the Filecoin and/or PL Network in 2022? How about in 2024? Tell me both the absolute numbers and the net increase / decrease between the two years.",
        answer_query="""
            SELECT 
                SUM(CASE WHEN EXTRACT(YEAR FROM tm.sample_date) = 2022 THEN tm.amount ELSE 0 END) AS full_time_developers_2022, 
                SUM(CASE WHEN EXTRACT(YEAR FROM tm.sample_date) = 2024 THEN tm.amount ELSE 0 END) AS full_time_developers_2024, 
                SUM(CASE WHEN EXTRACT(YEAR FROM tm.sample_date) = 2024 THEN tm.amount ELSE 0 END) - 
                SUM(CASE WHEN EXTRACT(YEAR FROM tm.sample_date) = 2022 THEN tm.amount ELSE 0 END) 
                    AS full_time_developers_increase_decrease_2022_to_2024 
            FROM oso.timeseries_metrics_by_collection_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
                AND m.metric_name LIKE 'GITHUB_full_time_developers_yearly' 
            JOIN oso.collections_v1 AS c 
                ON tm.collection_id = c.collection_id 
                AND (
                    c.collection_name LIKE '%filecoin%' 
                    OR c.collection_name LIKE '%protocol-labs%'
                )
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["developer_activity", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="What collection is responsible for projects with the most PRs made ever?",
        answer_query="""
            SELECT 
                collection_name 
            FROM oso.key_metrics_by_collection_v0 AS km 
            JOIN oso.metrics_v0 AS m 
                ON km.metric_id = m.metric_id 
            JOIN oso.collections_v1 AS c 
                ON km.collection_id = c.collection_id 
            WHERE m.metric_name LIKE '%opened_pull_requests%' 
            ORDER BY km.amount DESC 
            LIMIT 1
        """,
        priority="P0",
        difficulty="medium",
        question_categories=["pr_and_issue_tracking", "project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which NPM packages are associated with projects that merged at least 50 pull requests this month?",
        answer_query="""
            WITH projects AS (
                SELECT 
                    project_id 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                    AND m.metric_name = 'GITHUB_merged_pull_requests_weekly' 
                WHERE 
                    tm.sample_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1' MONTH 
                    AND tm.sample_date < DATE_TRUNC('month', CURRENT_DATE) 
                GROUP BY project_id 
                HAVING SUM(tm.amount) >= 50
            )
            SELECT DISTINCT 
                s.to_package_artifact_name 
            FROM projects AS p 
            JOIN oso.sboms_v0 AS s 
                ON s.from_project_id = p.project_id 
            WHERE s.to_package_artifact_source = 'NPM'
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["dependencies_and_software", "pr_and_issue_tracking"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Give me projects that received a grant in the last year and published at least one GitHub release.",
        answer_query="""
            SELECT 
                project_id 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                tm.sample_date >= current_date - INTERVAL '1' YEAR 
            GROUP BY project_id 
            HAVING 
                SUM(CASE WHEN m.metric_name LIKE '%_funding_awarded_monthly' THEN tm.amount ELSE 0 END) > 0 
                AND SUM(CASE WHEN m.metric_name LIKE 'GITHUB_releases_monthly' THEN tm.amount ELSE 0 END) > 0
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["funding_and_grants", "repo_or_package_metrics"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which collections include projects that generated more than 1000 pull requests and over 10000 blockchain transactions all-time?",
        answer_query="""
            SELECT 
                collection_id 
            FROM oso.key_metrics_by_collection_v0 AS km 
            JOIN oso.metrics_v0 AS m 
                ON km.metric_id = m.metric_id 
            GROUP BY collection_id 
            HAVING 
                SUM(CASE WHEN m.metric_name LIKE '%opened_pull_requests%' THEN km.amount ELSE 0 END) > 1000 
                AND SUM(CASE WHEN m.metric_name LIKE '%transactions%' THEN km.amount ELSE 0 END) > 10000
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["project_or_collection", "pr_and_issue_tracking", "blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Find projects with more than 5 dependencies and fewer than 100 GitHub commits in the past 30 days.",
        answer_query="""
            WITH fewer_commits AS (
                SELECT 
                    project_id 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    tm.sample_date >= current_date - INTERVAL '30' DAY 
                GROUP BY project_id 
                HAVING 
                    SUM(CASE WHEN m.metric_name LIKE '%commits_daily' THEN tm.amount ELSE 0 END) < 100
            )
            SELECT 
                project_id 
            FROM oso.sboms_v0 AS s 
            JOIN fewer_commits AS fc 
                ON s.from_project_id = fc.project_id 
            GROUP BY project_id 
            HAVING COUNT(DISTINCT to_package_artifact_id) > 5
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["developer_activity", "dependencies_and_software"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="List projects that had over $50K in funding and recorded at least 1000 contract invocations on Base in the last 6 months.",
        answer_query="""
            SELECT 
                project_id 
            FROM oso.timeseries_metrics_by_project_v0 AS tm 
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
            WHERE 
                tm.sample_date >= current_date - INTERVAL '6' MONTH 
            GROUP BY project_id 
            HAVING 
                SUM(CASE WHEN m.metric_name LIKE '%funding_awarded_monthly' THEN tm.amount ELSE 0 END) > 50000 
                AND SUM(CASE WHEN m.metric_name LIKE 'BASE_contract_invocations_monthly' THEN tm.amount ELSE 0 END) > 1000
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["funding_and_grants", "blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Show me all projects in the “gitcoin-oss” collection along with their total forks and total Ethereum gas used.",
        answer_query="""
            SELECT 
                km.project_id, 
                SUM(CASE WHEN m.metric_name LIKE 'GITHUB_forks_over_all_time' THEN km.amount ELSE 0 END) AS total_forks, 
                SUM(CASE WHEN m.metric_name LIKE '%gas_fees%' THEN km.amount ELSE 0 END) AS total_ethereum_gas_used 
            FROM oso.key_metrics_by_project_v0 AS km 
            JOIN oso.metrics_v0 AS m 
                ON km.metric_id = m.metric_id 
            JOIN oso.projects_by_collection_v1 AS pbc 
                ON km.project_id = pbc.project_id 
            JOIN oso.collections_v1 AS c 
                ON pbc.collection_id = c.collection_id 
            WHERE c.collection_name LIKE 'gitcoin-oss' 
            GROUP BY km.project_id
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["repo_or_package_metrics", "blockchain_activity", "project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="List projects that published at least one new release in the last 6 months and had a user operation via paymaster in ERC-4337.",
        answer_query="""
            WITH recieved_grants AS (
                SELECT 
                    project_id 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE tm.sample_date >= current_date - INTERVAL '6' MONTH 
                GROUP BY project_id 
                HAVING SUM(CASE WHEN m.metric_name LIKE 'GITHUB_releases_monthly' THEN tm.amount ELSE 0 END) > 0
            ), 
            paymaster_projects AS (
                SELECT DISTINCT 
                    a.project_id 
                FROM oso.int_events_daily__4337 AS e 
                JOIN oso.artifacts_by_project_v1 AS a 
                    ON e.to_artifact_id = a.artifact_id 
                WHERE e.event_type LIKE 'CONTRACT_INVOCATION_VIA_PAYMASTER'
            ) 
            SELECT DISTINCT 
                rg.project_id 
            FROM recieved_grants AS rg 
            JOIN paymaster_projects AS pp 
                ON rg.project_id = pp.project_id
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["repo_or_package_metrics", "blockchain_activity"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which collection has seen the most TVL growth over the last year to now?",
        answer_query="""
            WITH tvl_data AS (
                SELECT 
                    pc.collection_name, 
                    SPLIT_PART(m.metric_name, '_', 1) AS chain, 
                    tm.sample_date AS bucket_day, 
                    tm.amount AS tvl 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                    AND m.metric_name LIKE '%defillama_tvl_daily' 
                JOIN oso.projects_by_collection_v1 AS pc 
                    ON tm.project_id = pc.project_id 
                WHERE tm.sample_date BETWEEN current_date - INTERVAL '1' YEAR AND current_date
            ), 
            year_window AS (
                SELECT 
                    collection_name, 
                    chain, 
                    max_by(tvl, bucket_day) - min_by(tvl, bucket_day) AS tvl_growth 
                FROM tvl_data 
                GROUP BY collection_name, chain
            ) 
            SELECT 
                collection_name, 
                MAX(tvl_growth) AS max_tvl_growth 
            FROM year_window 
            GROUP BY collection_name 
            ORDER BY max_tvl_growth DESC 
            LIMIT 1
        """,
        priority="P2",
        difficulty="hard",
        question_categories=["blockchain_activity", "comparative_or_trend_analysis", "project_or_collection"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Give me all of the collections that are in the top 10% for projects associated with them.",
        answer_query="""
            WITH collection_counts AS (
                SELECT 
                    collection_id, 
                    COUNT(DISTINCT project_id) AS project_count 
                FROM oso.projects_by_collection_v1 
                GROUP BY collection_id
            ), 
            ranked AS (
                SELECT 
                    collection_id, 
                    project_count, 
                    CUME_DIST() OVER (ORDER BY project_count) AS cume_dist 
                FROM collection_counts
            ) 
            SELECT 
                collection_id 
            FROM ranked 
            WHERE cume_dist >= 0.90
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["project_or_collection", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="What 5 projects have the most open issues over the last month? Compare this with the 5 projects with the most open issues over the last 3 months. Return them as one table side by side so I can compare the projects and their counts",
        answer_query="""
            WITH pastmonth_issues AS (
                SELECT 
                    tm.project_id, 
                    SUM(tm.amount) AS open_issues, 
                    ROW_NUMBER() OVER (ORDER BY SUM(tm.amount) DESC) AS rn 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    m.metric_name = 'GITHUB_opened_issues_weekly' 
                    AND tm.sample_date >= CURRENT_DATE - INTERVAL '1' MONTH 
                GROUP BY tm.project_id
            ), 
            pastthreemonths_issues AS (
                SELECT 
                    tm.project_id, 
                    SUM(tm.amount) AS open_issues, 
                    ROW_NUMBER() OVER (ORDER BY SUM(tm.amount) DESC) AS rn 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    m.metric_name = 'GITHUB_opened_issues_monthly' 
                    AND tm.sample_date >= CURRENT_DATE - INTERVAL '4' MONTH 
                    AND tm.sample_date < CURRENT_DATE - INTERVAL '1' MONTH 
                GROUP BY tm.project_id
            ) 
            SELECT 
                c.project_id AS pastmonth_project_id, 
                c.open_issues AS pastmonth_open_issues, 
                l.project_id AS pastthreemonths_project_id, 
                l.open_issues AS pastthreemonths_open_issues 
            FROM pastmonth_issues AS c 
            FULL OUTER JOIN pastthreemonths_issues AS l 
                ON c.rn = l.rn 
            WHERE (c.rn <= 5 OR l.rn <= 5) 
            ORDER BY coalesce(c.rn, l.rn)
        """,
        priority="P1",
        difficulty="hard",
        question_categories=["pr_and_issue_tracking", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="What projects saw any growth in their TVL from 2025 so far compared with the end of 2024?",
        answer_query="""
            WITH tvl_data AS (
                SELECT 
                    tm.project_id, 
                    SPLIT_PART(m.metric_name, '_', 1) AS chain, 
                    tm.sample_date AS bucket_day, 
                    tm.amount AS tvl 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                    AND m.metric_name LIKE '%defillama_tvl_daily' 
                JOIN oso.projects_by_collection_v1 AS pc 
                    ON tm.project_id = pc.project_id 
                WHERE tm.sample_date BETWEEN DATE '2024-12-31' AND current_date
            ), 
            tvl_end_2024 AS (
                SELECT 
                    project_id, 
                    chain, 
                    SUM(tvl) AS tvl_end_2024 
                FROM tvl_data 
                WHERE bucket_day = DATE '2024-12-31' 
                GROUP BY project_id, chain
            ), 
            tvl_latest_2025 AS (
                SELECT 
                    project_id, 
                    chain, 
                    max_by(tvl, bucket_day) AS tvl_latest_2025 
                FROM tvl_data 
                WHERE bucket_day BETWEEN DATE '2025-01-01' AND current_date 
                GROUP BY project_id, chain
            ) 
            SELECT DISTINCT 
                e.project_id 
            FROM tvl_end_2024 AS e 
            JOIN tvl_latest_2025 AS l 
                ON e.project_id = l.project_id 
                AND e.chain = l.chain 
            WHERE (l.tvl_latest_2025 - e.tvl_end_2024) > 0
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["blockchain_activity", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="List projects that have increased forks year over year for the past 3 years and are in the top 20% for GitHub stars (all time).",
        answer_query="""
            WITH forks_2022 AS (
                SELECT 
                    tm.project_id, 
                    max_by(tm.amount, tm.sample_date) AS forks_2022 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    m.metric_name LIKE '%forks_daily' 
                    AND tm.sample_date BETWEEN DATE '2022-01-01' AND DATE '2022-12-31' 
                GROUP BY tm.project_id
            ), 
            forks_2023 AS (
                SELECT 
                    tm.project_id, 
                    max_by(tm.amount, tm.sample_date) AS forks_2023 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    m.metric_name LIKE '%forks_daily' 
                    AND tm.sample_date BETWEEN DATE '2023-01-01' AND DATE '2023-12-31' 
                GROUP BY tm.project_id
            ), 
            forks_2024 AS (
                SELECT 
                    tm.project_id, 
                    max_by(tm.amount, tm.sample_date) AS forks_2024 
                FROM oso.timeseries_metrics_by_project_v0 AS tm 
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                WHERE 
                    m.metric_name LIKE '%forks_daily' 
                    AND tm.sample_date BETWEEN DATE '2024-01-01' AND DATE '2024-12-31' 
                GROUP BY tm.project_id
            ), 
            forks_growth AS (
                SELECT 
                    f22.project_id, 
                    f22.forks_2022, 
                    f23.forks_2023, 
                    f24.forks_2024 
                FROM forks_2022 AS f22 
                JOIN forks_2023 AS f23 
                    ON f22.project_id = f23.project_id 
                JOIN forks_2024 AS f24 
                    ON f22.project_id = f24.project_id
            ), 
            stars AS (
                SELECT 
                    km.project_id, 
                    max(km.amount) AS stars_alltime 
                FROM oso.key_metrics_by_project_v0 AS km 
                JOIN oso.metrics_v0 AS m 
                    ON km.metric_id = m.metric_id 
                WHERE m.metric_name LIKE '%stars_over_all_time' 
                GROUP BY km.project_id
            ), 
            stars_ranked AS (
                SELECT 
                    project_id, 
                    stars_alltime, 
                    CUME_DIST() OVER (ORDER BY stars_alltime) AS cume_dist 
                FROM stars
            ) 
            SELECT 
                fg.project_id 
            FROM forks_growth AS fg 
            JOIN stars_ranked AS s 
                ON fg.project_id = s.project_id 
            WHERE 
                fg.forks_2022 < fg.forks_2023 
                AND fg.forks_2023 < fg.forks_2024 
                AND s.cume_dist >= 0.80
        """,
        priority="P2",
        difficulty="hard",
        question_categories=["repo_or_package_metrics", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Show me projects where last week's opened-issue count was higher than their transaction count for the same period.",
        answer_query="""
            WITH weekly_counts AS (
                SELECT 
                    tm.project_id,
                    SUM(CASE WHEN m.metric_name LIKE '%opened_issues_daily' THEN tm.amount ELSE 0 END) AS opened_issues_count,
                    SUM(CASE WHEN m.metric_name LIKE '%transactions_daily' THEN tm.amount ELSE 0 END) AS transactions_count
                FROM oso.timeseries_metrics_by_project_v0 AS tm
                JOIN oso.metrics_v0 AS m
                    ON tm.metric_id = m.metric_id
                WHERE 
                    tm.sample_date BETWEEN CURRENT_DATE - INTERVAL '7' DAY AND CURRENT_DATE - INTERVAL '1' DAY
                GROUP BY tm.project_id
            )
            SELECT 
                project_id,
                opened_issues_count,
                transactions_count
            FROM weekly_counts
            WHERE opened_issues_count > transactions_count
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["repo_or_package_metrics", "comparative_or_trend_analysis"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Which projects have a dependency count above the overall average and average daily TVL growth for the last year above 5%?",
        answer_query="""
            WITH dependency_counts AS (
                SELECT 
                    from_project_id AS project_id, 
                    COUNT(DISTINCT to_package_artifact_id) AS dependency_count
                FROM oso.sboms_v0
                GROUP BY from_project_id
            ),
            avg_dep AS (
                SELECT 
                    AVG(dependency_count) AS avg_dependency 
                FROM dependency_counts
            ),
            tvl_lag AS (
                SELECT 
                    project_id, 
                    bucket_day, 
                    amount AS tvl,
                    LAG(amount) OVER (PARTITION BY project_id ORDER BY bucket_day) AS prev_tvl
                FROM oso.int_events_daily_to_project__defillama_tvl
                WHERE bucket_day >= CURRENT_DATE - INTERVAL '1' YEAR
            ),
            daily_pct AS (
                SELECT 
                    project_id, 
                    (tvl - prev_tvl) / prev_tvl AS daily_pct_change
                FROM tvl_lag
                WHERE prev_tvl > 0
            ),
            avg_daily_growth AS (
                SELECT 
                    project_id, 
                    AVG(daily_pct_change) AS avg_daily_growth
                FROM daily_pct
                GROUP BY project_id
            )
            SELECT 
                dc.project_id, 
                dc.dependency_count, 
                ag.avg_daily_growth
            FROM dependency_counts AS dc
            JOIN avg_dep AS ad ON dc.dependency_count > ad.avg_dependency
            JOIN avg_daily_growth AS ag ON dc.project_id = ag.project_id
            WHERE ag.avg_daily_growth > 0.05
        """,
        priority="P1",
        difficulty="hard",
        question_categories=["blockchain_activity", "comparative_or_trend_analysis", "dependencies_and_software"],
        real_user_question=False
    ),
    create_text2sql_example(
        question="Has the DeFi project Compound Finance had a significant increase in TVL on Base between October 2024 and March 2025?",
        answer_query="""
            WITH tvl_data AS (
                SELECT 
                    tm.sample_date AS bucket_day, 
                    tm.amount AS tvl
                FROM oso.timeseries_metrics_by_project_v0 AS tm
                JOIN oso.metrics_v0 AS m 
                    ON tm.metric_id = m.metric_id 
                    AND m.metric_name LIKE 'BASE_defillama_tvl_daily'
                JOIN oso.projects_v1 AS p 
                    ON tm.project_id = p.project_id
                WHERE 
                    LOWER(p.display_name) LIKE '%compound finance%' 
                    AND tm.sample_date BETWEEN DATE '2024-10-01' AND DATE '2025-03-31'
            ),
            tvl_snapshots AS (
                SELECT 
                    min_by(tvl, bucket_day) AS tvl_oct2024, 
                    max_by(tvl, bucket_day) AS tvl_mar2025
                FROM tvl_data
            )
            SELECT 
                tvl_oct2024, 
                tvl_mar2025, 
                (tvl_mar2025 - tvl_oct2024) AS absolute_change,
                CASE 
                    WHEN tvl_oct2024 = 0 THEN NULL 
                    ELSE 100.0 * (tvl_mar2025 - tvl_oct2024) / tvl_oct2024 
                END AS pct_change
            FROM tvl_snapshots
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["comparative_or_trend_analysis", "blockchain_activity"],
        real_user_question=True
    ),
    create_text2sql_example(
        question="Show me the projects (sorted by the number of stars they've received) that are active in both the Solana and Arbitrum ecosystems.",
        answer_query="""
            SELECT tm.project_id
            FROM oso.timeseries_metrics_by_project_v0 AS tm
            JOIN oso.metrics_v0 AS m 
                ON tm.metric_id = m.metric_id 
                AND m.metric_name = 'GITHUB_full_time_developers_monthly'
            JOIN oso.projects_by_collection_v1 AS pbc 
                ON tm.project_id = pbc.project_id
            WHERE tm.sample_date >= current_date - INTERVAL '3' MONTH
            GROUP BY tm.project_id
            HAVING SUM(tm.amount) > 0
        """,
        priority="P1",
        difficulty="medium",
        question_categories=["developer_activity", "project_or_collection", "repo_or_package_metrics"],
        real_user_question=False
    )
]
