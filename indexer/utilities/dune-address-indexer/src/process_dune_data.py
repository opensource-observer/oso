from dotenv import load_dotenv
import json
import os
import pandas as pd
import requests
from web3 import Web3


load_dotenv()


ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']
APIS = {
    'optimism': {
        'etherscan': f'https://api-optimistic.etherscan.io/api',
        'alchemy': f'https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    },
    'mainnet': {
        'etherscan': 'https://api.etherscan.io/api',
        'alchemy': f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    }
}
PATH_TO_CONTRACTS = "data/dune_exports/contracts.csv"
PATH_TO_FACTORIES = "data/dune_exports/factories.csv"
JSON_PATH = "data/dune_addresses.json"


def is_eoa(chain, address):
    
    url = APIS[chain]['alchemy']
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "params": [address, "latest"],
        "method": "eth_getCode"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Error looking up address {address}")
        return None
    result = response.json()['result']
    return result == '0x'


def fetch_contract_name(chain, address):    
    
    try:
        url = APIS[chain]['etherscan']
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': ETHERSCAN_API_KEY
        }
        response = requests.get(url, params=params)
        if response.json()['status'] != '1':
            print(f"Error looking up a contract at address {address}")
            return None

        contract_name = response.json()['result'][0]['ContractName']
        if not contract_name:
            print(f"No contract/name associated with address {address}")
            return None
        
        print(f"{chain}: {address} -> {contract_name}")
        return contract_name    
    except:
        print(f"\n\n** Fatal error looking up a contract at address {address}\n\n")
        return None


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


def process_dune_data(contracts_path, factories_path, output_path):
    
    addresses = load_and_prepare_data(contracts_path, 'created_time', 'creator_address', ['creator'])
    print(f"Processing {len(addresses)} creator addresses.")
    for address, info in addresses.items():
        eoa = is_eoa('optimism', address)
        info['tags'] = ['creator', 'eoa'] if eoa else ['contract', 'factory']
        if not eoa:
            info['name'] = fetch_contract_name('optimism', address)

    factories = load_and_prepare_data(factories_path, 'created_time_earliest', 'contract_creator_if_factory', ['factory', 'contract'])
    print(f"Processing {len(factories)} factory addresses.")
    update_address_info(addresses, factories, 'optimism')
    
    contracts = load_and_prepare_data(contracts_path, 'created_time', 'contract_address', ['contract'])
    print(f"Processing {len(contracts)} contract addresses.")
    update_address_info(addresses, contracts, 'optimism')

    deduplicate_info(addresses)

    with open(output_path, 'w') as outfile:
        json.dump(addresses, outfile, indent=4)


if __name__ == "__main__":
    process_dune_data(PATH_TO_CONTRACTS, PATH_TO_FACTORIES, JSON_PATH)
