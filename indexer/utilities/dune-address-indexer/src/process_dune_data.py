import argparse
import json
import pandas as pd

from address_tagging import is_eoa, fetch_contract_name

PATH_TO_CONTRACTS = "data/dune_exports/contracts.csv"
PATH_TO_FACTORIES = "data/dune_exports/factories.csv"
JSON_PATH = "data/dune_exports/addresses.json"


def load_and_prepare_data(path, time_col_name, address_col_name, tags_list):
    
    df = pd.read_csv(path)
    df.rename(columns={time_col_name: 'event_time'}, inplace=True)
    df.sort_values(by='event_time', inplace=True)

    addresses = {}
    for row in df.to_dict('records'):
        addr = row[address_col_name]
        if not addr or not isinstance(addr, str):
            continue
        if addr in addresses:
            addresses[addr]['project_list'].append(row['contract_project'])
        else:
            addresses[addr] = {
                "project_list": [row.get('contract_project', None)],
                "event_time": row['event_time'],
                "tags": tags_list
            }
    return addresses


def update_address_info(addresses, new_data, chain):
    
    for address, info in new_data.items():
        if address not in addresses:
            addresses[address] = info
            addresses[address]['name'] = fetch_contract_name(chain, address) if 'name' not in info else info['name']
        else:
            addresses[address]['project_list'].extend(info['project_list'])
            addresses[address]['tags'].extend(info['tags'])


def deduplicate_info(addresses):
    
    for address, info in addresses.items():
        addresses[address]['project_list'] = list(set(info['project_list']))
        addresses[address]['tags'] = list(set(info['tags']))


def process_dune_data(chain, contracts_path, factories_path, output_path):
    
    addresses = load_and_prepare_data(contracts_path, 'created_time', 'creator_address', ['creator'])
    print(f"Processing {len(addresses)} creator addresses.")
    for address, info in addresses.items():
        eoa = is_eoa(chain, address)
        info['tags'] = ['creator', 'eoa'] if eoa else ['contract', 'factory']
        if not eoa:
            info['name'] = fetch_contract_name(chain, address)

    factories = load_and_prepare_data(factories_path, 'created_time_earliest', 'contract_creator_if_factory', ['factory', 'contract'])
    print(f"Processing {len(factories)} factory addresses.")
    update_address_info(addresses, factories, chain)
    
    contracts = load_and_prepare_data(contracts_path, 'created_time', 'contract_address', ['contract'])
    print(f"Processing {len(contracts)} contract addresses.")
    update_address_info(addresses, contracts, chain)

    deduplicate_info(addresses)

    with open(output_path, 'w') as outfile:
        json.dump(addresses, outfile, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process Dune data.')
    parser.add_argument('--chain', dest='chain', required=True, help='Select a chain to process (mainnet or optimism)')
    parser.add_argument('--contracts', dest='contracts_path', required=True, help='Path to contracts CSV file')
    parser.add_argument('--factories', dest='factories_path', required=True, help='Path to factories CSV file')
    parser.add_argument('--output', dest='output_path', required=True, help='Path to output JSON file')

    args = parser.parse_args()
    process_dune_data(args.chain, args.contracts_path, args.factories_path, args.output_path)

    # test
    # python src/process_dune_data.py --chain=optimism --contracts=data/dune_exports/contracts.csv --factories=data/dune_exports/factories.csv --output=data/dune_exports/addresses.json