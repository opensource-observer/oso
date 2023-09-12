import argparse
import json
import pandas as pd
import requests

from address_tagging import is_eoa, fetch_contract_name


# https://github.com/gitcoinco/allo-indexer
CHAINSAUCE_URL = "https://indexer-grants-stack.gitcoin.co/data/"
CHAIN_IDS = {
    '1': 'mainnet',
    '10': 'optimism',
    '250': 'fantom',
    '42161': 'arbitrum one',
    '424': 'pgn'
}

def get_rounds(chain_num):

    round_url = "/".join([CHAINSAUCE_URL, chain_num, "rounds.json"])
    r = requests.get(round_url)
    round_data = r.json()
    
    funding_round_data = []
    for r in round_data:
        if r.get('metadata') and r['metadata'].get('name'):
            funding_round_data.append({
                "roundId": r['id'],
                "roundName": r['metadata']['name'],
            })    
        else:
            print(f"Skipping round {r['id']} on chain {chain_num} because it has no metadata.")
    return funding_round_data
    

def get_projects(chain_num, funding_round_data):
    
    projects_data = []
    for funding_round in funding_round_data:
        round_id = funding_round['roundId']
        round_name = funding_round['roundName']
        print(f"Gathering projects data for round: {round_name}...")

        url = "/".join([CHAINSAUCE_URL, chain_num, "rounds", round_id, "applications.json"])
        projects_json = requests.get(url).json()

        for project in projects_json:
                        
            if project['status'] != "APPROVED":
                continue

            if not project.get('metadata'):
                continue

            name = project['metadata']['application']['project']['title']
            address = project['metadata']['application']['recipient']
            github = project['metadata']['application']['project'].get('projectGithub', None)
            
            projects_data.append({
                'name': name,
                'address': address,
                'projectGithub': github,
                'fundingRounds': round_name,
                'chain': chain_num
            })
            print(f"Normalized data for project: {name}")

    print(f"Obtained {len(projects_data)} projects on Chain {chain_num}.")

    return projects_data


def get_all_projects_in_round(chain_nums):

    all_projects = []
    for chain_id in chain_nums:
        funding_round_data = get_rounds(chain_id)        
        all_projects.extend(get_projects(chain_id, funding_round_data))
        
    df = pd.DataFrame(all_projects)
    return df


def github_handle_to_url(handle):
    if not handle or not isinstance(handle, str) or 'gitcoinco' in handle:
        return None
    handle = handle.strip()
    if len(handle) < 3:
        return None
    if "https://github.com" in handle:
        return handle
    return f"https://github.com/{handle}"


def get_oss_projects(df_path):

    df = pd.read_csv(df_path)
    df['projectGithub'] = df['projectGithub'].apply(github_handle_to_url)
    df = df[df['projectGithub'].notnull()]
    df['chainAddress'] = df.apply(lambda x: f"{x['chain']}: {x['address']}", axis=1)
    df.drop_duplicates(subset=['projectGithub', 'chainAddress'], inplace=True)
    df['chain'] = df['chain'].apply(lambda x: CHAIN_IDS[str(x)])

    githubs = df['projectGithub'].unique().tolist()
    project_data = []
    for gh in githubs:
        dff = df[df['projectGithub'] == gh]
        addresses = dff.groupby('chain')['address'].apply(list)
        addresses_dict = {}
        for chain, address_list in addresses.items():
            for addr in address_list: 
                tags = ['wallet']
                eoa = is_eoa(chain, addr)
                if eoa:
                    tags.append('eoa')
                else:
                    contract = fetch_contract_name(chain, addr)
                    if contract and ("Safe" in contract or contract == "Proxy"):
                        tags.append('safe')        
                addresses_dict[chain] = {
                    'address': addr,
                    'tags': tags
                }
        p = {'name': dff['name'].iloc[0], 'github': {"url": gh}, **addresses_dict}            
        project_data.append(p)
        ##print(f"Normalized data for project: {p}")
    return project_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get all OSS projects.')
    parser.add_argument('--reindex', dest='reindex', action='store_true', help='Whether to reindex data')
    parser.add_argument('--csv_output', dest='csv_output', required=True, help='Path to save the CSV output')
    parser.add_argument('--json_output', dest='json_output', required=True, help='Path to save the JSON output')
    
    args = parser.parse_args()
    
    if args.reindex:
        df = get_all_projects_in_round(CHAIN_IDS.keys())    
        df.to_csv(args.csv_output, index=False)

    project_data = get_oss_projects(args.csv_output)
    with open(args.json_output, 'w') as outfile:
        json.dump(project_data, outfile, indent=4)

    # test
    # python src/get_allo_projects.py --reindex --csv_output=data/allo/projects.csv --json_output=data/allo/oss-projects.json
    # python src/get_allo_projects.py --csv_output=data/allo/projects.csv --json_output=data/allo/oss-projects.json