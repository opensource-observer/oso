import requests
import polars as pl
from dagster import multi_asset, AssetOut, Output
from typing import Any, Dict, List
import time

@multi_asset(
    outs={
        "giveth__qf_rounds_v3": AssetOut(),
        "giveth__projects_by_round_v3": AssetOut(),
    },
)
def fetch_giveth_data():
    endpoint = "https://mainnet.serve.giveth.io/graphql"
    
    def run_query(query: str, variables: Dict[str, Any], retries: int = 3) -> Dict[str, Any]:
        for attempt in range(retries):
            try:
                response = requests.post(
                    endpoint,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()["data"]
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

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
        allocatedTokenSymbol
        beginDate
        endDate
      }
    }
    """
    
    # Projects Query
    projects_query = """
    query GetProjects($qfRoundId: Int!, $skip: Int!, $take: Int!) {
      allProjects(qfRoundId: $qfRoundId, skip: $skip, take: $take) {
        projects {
          id
          title
          description
          website
          walletAddress
          verified
          qfRounds { id }
        }
      }
    }
    """

    # Fetch QF Rounds
    qf_rounds_data = run_query(qf_rounds_query, {"activeOnly": False})["qfRounds"]
    qf_rounds_df = pl.DataFrame(qf_rounds_data)
    yield Output(qf_rounds_df, output_name="giveth__qf_rounds_v3")

    # Fetch Projects for each round
    all_projects = []
    for round_data in qf_rounds_data:
        skip = 0
        while True:
            variables = {
                "qfRoundId": round_data["id"],
                "skip": skip,
                "take": 50
            }
            result = run_query(projects_query, variables)
            projects = result["allProjects"]["projects"]
            if not projects:
                break
            all_projects.extend(projects)
            skip += len(projects)

    projects_df = pl.DataFrame(all_projects)
    yield Output(projects_df, output_name="giveth__projects_by_round_v3")