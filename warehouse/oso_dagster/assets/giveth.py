import requests
import polars as pl
from dagster import multi_asset, AssetOut, Output
from typing import Any

@multi_asset(
    outs={
        "giveth__qf_rounds_v2": AssetOut(),
        "giveth__projects_by_round_v2": AssetOut(),
    },
)

def fetch_giveth_data():
    endpoint = "https://mainnet.serve.giveth.io/graphql"

    def run_query(query, variables, retries=3, delay=5):
        import time
        for attempt in range(retries):
            try:
                response = requests.post(endpoint, json={"query": query, "variables": variables})
                response.raise_for_status()
                json_data = response.json()
                if "data" not in json_data or json_data["data"] is None:
                    raise ValueError(f"No 'data' field in response: {json_data}")
                return json_data["data"]
            except (requests.exceptions.RequestException, ValueError) as e:
                if attempt < retries - 1:
                    print(f"[Retry {attempt+1}] Giveth API failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise

    def flatten_dict(d: dict[str, Any], parent_key: str = '', sep: str = '_') -> dict[str, Any]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def align_columns(data: list[dict]) -> pl.DataFrame:
        # Get all unique keys across all rows
        all_keys = sorted(set().union(*(row.keys() for row in data)))
        # Ensure every row has all keys (fill with None)
        aligned_data = [
            {key: row.get(key, None) for key in all_keys}
            for row in data
        ]
        return pl.DataFrame(aligned_data, schema=all_keys)

    # QF Rounds Query
    qf_rounds_query = """
    query GetRounds($activeOnly: Boolean!) {
      qfRounds(activeOnly: $activeOnly) {
          id
          name
          title
          description
          slug
          isActive
          allocatedFund
          allocatedFundUSD
          allocatedFundUSDPreferred
          allocatedTokenSymbol
          allocatedTokenChainId
          maximumReward
          minimumPassportScore
          minMBDScore
          minimumValidUsdValue
          eligibleNetworks
          beginDate
          endDate
          qfStrategy
          bannerBgImage
          sponsorsImgs
          isDataAnalysisDone
          clusterMatchingSyncAt 
      }
    }
    """
    qf_rounds_result = run_query(qf_rounds_query, {"activeOnly": False})
    if not qf_rounds_result or "qfRounds" not in qf_rounds_result:
        raise ValueError("Invalid response: 'qfRounds' key is missing or response is None")
    qf_rounds = qf_rounds_result["qfRounds"]
    qf_rounds_flat = [flatten_dict(r) for r in qf_rounds]
    qf_rounds_df = align_columns(qf_rounds_flat)
    print("QF Rounds DF schema:")
    print(qf_rounds_df.schema)
    print("QF Rounds DF preview:")
    print(qf_rounds_df.head(3))

    yield Output(qf_rounds_df, output_name="giveth__qf_rounds_v2")

    # Projects Query
    projects_query = """
    query GetProjects($qfRoundId: Int!, $skip: Int!, $take: Int!) {
      allProjects(qfRoundId: $qfRoundId, skip: $skip, take: $take, orderBy: {
        field: CreationDate,
        direction: DESC
      }) {
        projects {
          id
          title
          slug
          slugHistory
          description
          descriptionSummary
          traceCampaignId
          givingBlocksId
          changeId
          website
          youtube
          creationDate
          updatedAt
          latestUpdateCreationDate
          organization { id name website }
          coOrdinates
          image
          impactLocation
          categories {
            id
          }
          qfRounds {
            id
            title
          }
          balance
          stripeAccountId
          walletAddress
          verified
          verificationStatus
          isImported
          giveBacks
          donations {
            id
          }
          qualityScore
          contacts {
            url
          }
          reactions{
            id
          }
          addresses {
            id
          }
          socialMedia {
            id
          }
          anchorContracts {
            id
          }
          status{
            id
            name
          }
          adminUserId
          statusHistory {
            id
          }
          projectVerificationForm {
            id
          }
          featuredUpdate {
            id
          }
          verificationFormStatus
          socialProfiles { id name link socialNetwork isVerified }
          projectEstimatedMatchingView { projectId qfRoundId }
          totalDonations
          totalTraceDonations
          totalReactions
          totalProjectUpdates
          sumDonationValueUsdForActiveQfRound
          countUniqueDonorsForActiveQfRound
          countUniqueDonors
          listed
          isGivbackEligible
          reviewStatus
          projectUrl
          prevStatusId
          adminJsBaseUrl
          campaigns {
              id
              slug
              title
              type
              isActive
              isNew
              isFeatured
              description
              hashtags
              relatedProjectsSlugs
              landingLink
              updatedAt
              createdAt
          }
          estimatedMatching {
            projectDonationsSqrtRootSum
            allProjectsSum
            matchingPool
            matching
          }
        }
      }
    }
    """

    all_projects = []
    for round_ in qf_rounds:
        round_id = round_["id"]
        skip = 0
        while True:
            projects_result = run_query(projects_query, {
                "qfRoundId": int(round_id),
                "skip": skip,
                "take": 50
            })
            if not projects_result or "allProjects" not in projects_result:
                break
            page = projects_result["allProjects"].get("projects", [])
            if not page:
                break
            all_projects.extend([flatten_dict(p) for p in page])
            skip += 50

    projects_df = align_columns(all_projects)
    print("Projects DF schema:")
    print(projects_df.schema)
    print("Projects DF preview:")
    print(projects_df.head(3))
    yield Output(projects_df, output_name="giveth__projects_by_round_v2")



from .graphql_updated import GraphQLResourceConfig, graphql_factory

@multi_asset(
    outs={
        "giveth__projects_by_round_paginated": AssetOut(),
    },
)
def fetch_giveth_paginated():
    config = GraphQLResourceConfig(
        name="giveth_projects",
        endpoint="https://mainnet.serve.giveth.io/graphql",
        target_type="Project",
        target_query="allProjects",
        parameters={
            "qfRoundId": {"type": "Int!", "value": 65},
        },
        pagination={
            "method": "offset",
            "offset_param": "skip",
            "limit_param": "take",
            "page_size": 25,
            "start_offset": 0,
            "retries": 3,
        }
    )

    fetch_paginated = graphql_factory(config)
    yield Output(list(fetch_paginated().execute_in_process().output_for_node("giveth_projects")), output_name="giveth__projects_by_round_paginated")