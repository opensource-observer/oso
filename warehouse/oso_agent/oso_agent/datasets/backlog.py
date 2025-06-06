from typing import List

from ..types.datasets import BacklogQuestion, create_backlog_question

# stored questions that have yet to be implemented as official evals yet
QUESTION_BACKLOG: List[BacklogQuestion] = [
    create_backlog_question(
        question="Which projects in S7 have deployments on more than one chain?",
        real_user_question=True,
        notes="text2sql model"
    ),
    create_backlog_question(
        question="I'm looking for a list of the top 100 projects [in terms of gas fees generated over the last 6 months on the Superchain], but with an array of the top 10 contract addresses for each project.",
        real_user_question=True,
        answer="""
            "WITH metrics AS (
            SELECT
                p.display_name AS project_display_name,
                p.project_source,
                abp.artifact_name AS contract,
                SUM(tm.amount) AS gas_fees_total
            FROM timeseries_metrics_by_artifact_v0 AS tm
            JOIN metrics_v0 AS m ON tm.metric_id = m.metric_id
            JOIN artifacts_by_project_v1 AS abp ON tm.artifact_id = abp.artifact_id
            JOIN projects_v1 AS p ON abp.project_id = p.project_id
            WHERE
                m.metric_name IN (
            'BASE_GAS_FEES_MONTHLY','BOB_GAS_FEES_MONTHLY','FRAX_GAS_FEES_MONTHLY','INK_GAS_FEES_MONTHLY','KROMA_GAS_FEES_MONTHLY','LISK_GAS_FEES_MONTHLY','LYRA_GAS_FEES_MONTHLY','METAL_GAS_FEES_MONTHLY','MINT_GAS_FEES_MONTHLY','MODE_GAS_FEES_MONTHLY','OPTIMISM_GAS_FEES_MONTHLY','ORDERLY_GAS_FEES_MONTHLY','POLYNOMIAL_GAS_FEES_MONTHLY','RACE_GAS_FEES_MONTHLY','REDSTONE_GAS_FEES_MONTHLY','SHAPE_GAS_FEES_MONTHLY','SONEIUM_GAS_FEES_MONTHLY','SWAN_GAS_FEES_MONTHLY','SWELL_GAS_FEES_MONTHLY','UNICHAIN_GAS_FEES_MONTHLY','WORLDCHAIN_GAS_FEES_MONTHLY','XTERIO_GAS_FEES_MONTHLY','ZORA_GAS_FEES_MONTHLY'
                )
                AND tm.sample_date >= DATE('2025-01-01')
                AND tm.sample_date < DATE('2025-06-01')
            GROUP BY 1,2,3
            ),
            ranked_metrics AS (
            SELECT
                project_display_name,
                project_source,
                contract,
                gas_fees_total,
                ROW_NUMBER() OVER (
                PARTITION BY project_display_name, project_source
                ORDER BY gas_fees_total DESC
                ) AS rn
            FROM metrics
            ),
            top_metrics AS (
            SELECT
                project_display_name,
                project_source,
                contract
            FROM ranked_metrics
            WHERE rn <= 10
            ),
            project_totals AS (
            SELECT
                project_display_name,
                project_source,
                SUM(gas_fees_total) AS gas_fees_total
            FROM metrics
            GROUP BY 1, 2
            )
            SELECT
            pt.project_display_name,
            pt.project_source,
            pt.gas_fees_total,
            ARRAY_AGG(tm.contract) AS contracts
            FROM project_totals AS pt
            JOIN top_metrics AS tm
            ON pt.project_display_name = tm.project_display_name
            AND pt.project_source = tm.project_source
            GROUP BY pt.project_display_name, pt.project_source, pt.gas_fees_total
            ORDER BY pt.gas_fees_total DESC
            LIMIT 200""",
        notes="text2sql model - need to revisit answer after we implement new deduplication models"
    ),
    create_backlog_question(
        question='OLI has contracts labeled as "likely bot contracts" on Base, Uni etc. Can we see what percent of onchain activty these contracts contribute? Can we calculate the share of non-bot contract activity that is linked to Retro Funding projects on each chain?',
        real_user_question=True,
        notes="unsure of the right model"
    ),
    create_backlog_question(
        question="I want to have a list of all RF recipients of the last 3 months and some way to contact them.",
        real_user_question=True,
        notes="unsure of the right model"
    ),
    create_backlog_question(
        question="I'd like to come up with a set of filtering criteria for what Optimism calls \"mid-tail\" builders. These are projects that have deployed contracts on at least one of the Superchain chains, have open source GitHub repos with a track record of continuous activity, and are neither too big nor too small in terms of team size. Please propose a set of metrics that can be queried and then an initial set of heuristics we can use for identifying these so-called \"mid-tail\" builders.",
        real_user_question=True,
        notes="prob some sort of python/data science model"
    ),
    create_backlog_question(
        question="Which projects that have received funding from the Token House are in OSO? Which ones are in Atlas? What percentage of grants (in USD) from the Token House are mapped to projects in each source?",
        real_user_question=True,
        notes="prob some sort of python/data science model"
    ),
    create_backlog_question(
        question="Show me a breakdown of OP rewards by chain for Retro Funding: Onchain Builders. Create one version that weights by contract activity and another by TVL.",
        real_user_question=True,
        notes="prob some sort of python/data science model"
    ),
    create_backlog_question(
        question=" I want to lookup projects that are not yet in Atlas (just in OSO) that have contract addresses that are eligible for Retro Funding.",
        real_user_question=True,
        notes="docs agent"
    )
]