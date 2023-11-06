import pandas as pd
from address_lookup import is_eoa


PROJECT_SUMMARY_CSV = "data/project_attestation_summary.csv"	
PROJECT_OSSD_MAPPINGS = "data/rpgf3_ossd_mappings.csv"
CANONICAL_PROJECTS_LIST = "data/canonical_projects.csv"
PAYOUT_ADDRESS_CSV = "data/payout_addresses.csv"


def update_canonical_projects():

    df1 = pd.read_csv(PROJECT_OSSD_MAPPINGS, index_col='Project ID')
    df2 = pd.read_csv(PROJECT_SUMMARY_CSV, index_col='id')
    cols = ["applicantType", "contributionLinkCount", "impactMetricCount", "urlTypeCount"]
    df = df1.join(df2[cols], how='inner')

    try:
        df3 = pd.read_csv(PAYOUT_ADDRESS_CSV, index_col="Payout Address")
        df = df.join(df3, on='Payout Address', how='inner')
    except FileNotFoundError:
        print("Looking up EOA status for payout addresses...")
        df['isEOA'] = df['Payout Address'].apply(lambda x: is_eoa(chain='optimism', address=x, sleep=0.2))

    df = df[~df.index.duplicated(keep='first')]
    df.to_csv(CANONICAL_PROJECTS_LIST)
    print(f"Exported canonical projects list to: {CANONICAL_PROJECTS_LIST}")

if __name__ == "__main__":
    update_canonical_projects()
