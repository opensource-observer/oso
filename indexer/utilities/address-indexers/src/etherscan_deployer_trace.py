# experimental: etherscan-based approach of grabbing all contracts deployed by a project's address

import json
import os
import requests
from dotenv import load_dotenv
from web3 import Web3
from address_tagging import is_eoa, fetch_contract_name
from ossd import get_yaml_data_from_path, map_addresses_to_slugs
import time

load_dotenv()
ALCHEMY_API_KEY = os.environ['ALCHEMY_API_KEY']

APIS = {
    'optimism': {
        'etherscan': f'https://api-optimistic.etherscan.io/api',
        'etherscan_api_key': os.getenv("OP_ETHERSCAN_API_KEY"),
        'alchemy': f'https://opt-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    },
    'mainnet': {
        'etherscan': 'https://api.etherscan.io/api',
        'etherscan_api_key': os.getenv("ETHERSCAN_API_KEY"),
        'alchemy': f'https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}'
    }
}
DEFAULT_API = APIS['mainnet']
CONTRACT_CREATORS_DATA = "data/contract_creators/optimism.json"
PROJECT_SLUGS_DATA = "data/contract_creators/project_slugs.json"


def load_contract_creators_data():
    with open(CONTRACT_CREATORS_DATA, "r") as json_file:
        data = json.load(json_file)
    return data


def get_deploys_from_address(address, chain="optimism"):
    try:
        api = APIS.get(chain, DEFAULT_API)
        url = api['etherscan']
        api_key = api['etherscan_api_key']
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'apikey': api_key
        }
        response = requests.get(url, params=params)
        response_json = response.json()
        if response_json.get('status') != '1':
            print(f"Error looking up transactions at address {address} on {chain}")
            print(response.text)
            return None

        deployments = [tx['contractAddress'] for tx in response_json['result'] if not tx['to'] and tx['input'] and tx['isError'] == '0']
        return deployments
    except Exception as e:
        print(f"\n\n** Fatal error looking up transactions at address {address} on {chain}\n\n")
        print(e)
        return None


def load_project_mapping():
    with open(PROJECT_SLUGS_DATA, "r") as json_file:
        data = json.load(json_file)
    return data


def main():
    contract_creators_data = load_contract_creators_data()
    project_mapping = load_project_mapping()

    address_mapping = {}
    try:
        for addr, project in contract_creators_data.items():
            print(f"\nProcessing {addr} for {project}...")
            slug = project_mapping.get(project)
            if not slug:
                print(f"Skipping {addr} for {project} because no slug was found.")
                continue

            if project == "Gnosis Safe":
                continue

            if slug not in address_mapping:
                address_mapping[slug] = {"slug": slug, "blockchain": []}            

            if addr in [a['address'] for a in address_mapping[slug]["blockchain"]]:
                print(f"Skipping {addr} for {project} because it's already been added.")
                continue
            
            is_eoa_addr = is_eoa("optimism", addr)                            
            creator = {
                "address": addr,
                "tags": ["eoa" if is_eoa_addr else "contract"],
                "name": fetch_contract_name("optimism", addr) if not is_eoa_addr else None
            }   
                        
            blockchain_data = [creator]            
            deploys = get_deploys_from_address(addr)
            time.sleep(1)
            if deploys:
                creator["tags"].append("deployer")
                for deploy_address in deploys:
                    time.sleep(0.5)
                    contract_name = fetch_contract_name("optimism", deploy_address)
                    contract_deploys = get_deploys_from_address(deploy_address)
                    blockchain_data.append({
                        "address": deploy_address,
                        "tags": ["contract", "deployer"] if contract_deploys else ["contract"],
                        "name": contract_name
                    })

            address_mapping[slug]["blockchain"].extend(blockchain_data)
            with open("data/contract_creators/optimism_address_mapping.json", "w") as json_file:
                json.dump(address_mapping, json_file, indent=4)

    except:
        print(f"Error at project {project} with address {addr}")
    
    with open("data/contract_creators/optimism_address_mapping.json", "w") as json_file:
        json.dump(address_mapping, json_file, indent=4)

    # Print address_mapping or perform other operations as needed.

if __name__ == "__main__":
    main()
