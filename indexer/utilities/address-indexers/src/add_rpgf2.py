import json
import pandas as pd
from address_tagging import is_eoa, fetch_contract_name


def load_data(csv_path):
    """Load the CSV data into a DataFrame and filter the required columns."""
    df = pd.read_csv(csv_path)
    cols = [
        'Project',
        'profile_github',
        'address_cleaned',
        'Category',
        'Entity',
        'Address Type',
        'address_EthTxCount',
        'address_OpTxCount'
    ]
    return df[cols]


def get_networks_and_chain(row):
    """Determine the networks and chain based on the row data."""
    networks = []
    if row['address_EthTxCount'] > 0:
        networks.append('mainnet')
    if row['address_OpTxCount'] > 0:
        networks.append('optimism')

    # Default to 'optimism' if no networks are found
    if not networks:
        networks.append('optimism')
        
    return networks, networks[0]


def get_tags(row, chain):
    """Determine the tags for a blockchain address."""
    tags = ['wallet']

    if 'EOA' in row['Address Type']:
        if is_eoa(chain, row['address_cleaned']):
            tags.append('eoa')
        else:
            print(f"Error with EOA tag for project {row['Project']} and address {row['address_cleaned']}")
    else:
        contract_name = fetch_contract_name(chain, row['address_cleaned'])
        if isinstance(contract_name, str) and 'proxy' in contract_name.lower():
            tags.append('safe')
        else:
            print(f"Unknown contract for project {row['Project']} and address {row['address_cleaned']}")
            
    return tags


def create_json(df):
    """Create a JSON object from the DataFrame."""
    data = []
    
    for _, row in df.iterrows():
        github = row['profile_github']
        if not isinstance(github, str):
            continue

        networks, chain = get_networks_and_chain(row)
        tags = get_tags(row, chain)
        
        project = {
            "name": row['Project'],
            "github": {"url": github},
            row['address_cleaned']: {
                "tags": tags,
                "networks": networks
            }
        }
        data.append(project)
        
    return data


def dump_json(data, json_path):
    """Dump the data into a JSON file."""
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)


def main():
    csv_path = 'data/rpgf2/RPGF2 Tagged Projects - clean.csv'
    json_path = 'data/rpgf2/rpgf2.json'
    
    df = load_data(csv_path)
    json_data = create_json(df)
    dump_json(json_data, json_path)


if __name__ == "__main__":
    main()
