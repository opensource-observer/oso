import requests
import polars as pl
from dagster import multi_asset, AssetOut, Output

@multi_asset(
    outs={
        "giveth__qf_rounds": AssetOut(),
        "giveth__projects_by_round": AssetOut(),
    },
)
def fetch_giveth_data():
    endpoint = "https://mainnet.serve.giveth.io/graphql"

    def run_query(query, variables):
        response = requests.post(endpoint, json={"query": query, "variables": variables})
        response.raise_for_status()
        return response.json()["data"]

    # Fetch qfRounds
    qf_rounds_query = """
    query GetRounds($activeOnly: Boolean!) {
        qfRounds(activeOnly: $activeOnly) {
            id
            title
        }
    }
    """
    qf_rounds_result = run_query(qf_rounds_query, {"activeOnly": False})
    qf_rounds = qf_rounds_result["qfRounds"]

    # Convert to Polars DataFrame
    qf_rounds_df = pl.DataFrame(qf_rounds)
    yield Output(qf_rounds_df, output_name="giveth__qf_rounds")

    # Fetch projects for each round
    all_projects = []
    projects_query = """
    query GetProjects($qfRoundId: Int!, $skip: Int!, $take: Int!) {
      allProjects(qfRoundId: $qfRoundId, skip: $skip, take: $take, orderBy: {
        field: CreationDate,
        direction: DESC
      }) {
        projects {
          id
          title
          creationDate
        }
      }
    }
    """

    for round_ in qf_rounds:
        round_id = round_["id"]
        skip = 0
        while True:
            projects_result = run_query(projects_query, {
                "qfRoundId": int(round_id),
                "skip": skip,
                "take": 50
            })
            page = projects_result["allProjects"]["projects"]
            if not page:
                break
            all_projects.extend(page)
            skip += 50

    # Convert all projects to Polars DataFrame
    projects_df = pl.DataFrame(all_projects)
    yield Output(projects_df, output_name="giveth__projects_by_round")