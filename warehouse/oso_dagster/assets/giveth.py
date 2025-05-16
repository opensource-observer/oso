import requests
import polars as pl
from typing import Any
from dagster import multi_asset, AssetOut, Output
from ..factories.graphql import GraphQLResourceConfig, graphql_factory

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
    all_keys = sorted(set().union(*(row.keys() for row in data)))
    aligned_data = [
        {key: row.get(key, None) for key in all_keys}
        for row in data
    ]
    return pl.DataFrame(aligned_data, schema=all_keys)

@multi_asset(
    outs={
        "giveth__projects_by_round_paginated": AssetOut(),
        "giveth__qf_rounds_paginated": AssetOut()
    },
)
def fetch_giveth_projects_paginated():
    endpoint = "https://mainnet.serve.giveth.io/graphql"

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

    # Projects Query (included here for reference)
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
          categories { id }
          qfRounds { id title }
          balance
          stripeAccountId
          walletAddress
          verified
          verificationStatus
          isImported
          giveBacks
          donations { id }
          qualityScore
          contacts { url }
          reactions { id }
          addresses { id }
          socialMedia { id }
          anchorContracts { id }
          status { id name }
          adminUserId
          statusHistory { id }
          projectVerificationForm { id }
          featuredUpdate { id }
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

    response = requests.post(endpoint, json={"query": qf_rounds_query, "variables": {"activeOnly": False}})
    response.raise_for_status()
    data = response.json()
    qf_rounds = data.get("data", {}).get("qfRounds", [])

    all_projects = []

    for round_ in qf_rounds:
        round_id = round_["id"]

        config = GraphQLResourceConfig(
            name=f"giveth_projects_round_{round_id}",
            endpoint=endpoint,
            target_type="Project",
            target_query="allProjects",
            parameters={
                "qfRoundId": {"type": "Int!", "value": int(round_id)},
            },
            pagination={
                "method": "offset",
                "offset_param": "skip",
                "limit_param": "take",
                "page_size": 50,
                "start_offset": 0,
                "retries": 3
            },
            transform_fn=lambda result: result["allProjects"]["projects"]
        )

        gql_asset = graphql_factory(config)
        try:
            result = gql_asset().execute_in_process().output_for_node(config.name)
            all_projects.extend([flatten_dict(p) for p in result])
        except Exception as e:
            print(f"Failed to fetch projects for round {round_id}: {e}")

    projects_df = align_columns(all_projects)
    print("Projects DF schema:")
    print(projects_df.schema)
    print("Projects DF preview:")
    print(projects_df.head(3))
    yield Output(projects_df, output_name="giveth__projects_by_round_paginated")
    yield Output(pl.DataFrame(qf_rounds), output_name="giveth__qf_rounds_paginated")