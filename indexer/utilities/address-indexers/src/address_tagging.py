import csv
from dotenv import load_dotenv
import os
import requests
import time
from web3 import Web3


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

def is_eoa(chain, address, sleep=.5):
    
    url = APIS.get(chain, DEFAULT_API)['alchemy']
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
        print(f"Error looking up address {address} on {chain}")
        return None
    result = response.json()['result']
    time.sleep(sleep)
    return result == '0x'


def fetch_contract_name(chain, address, sleep=.5):    
    
    try:
        # TODO: this won't work for unmapped chains unless the project uses a deterministic deployer
        api = APIS.get(chain, DEFAULT_API)
        url = api['etherscan']
        api_key = api['etherscan_api_key']
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address,
            'apikey': api_key
        }
        response = requests.get(url, params=params)
        if response.json()['status'] != '1':
            print(f"Error looking up a contract at address {address} on {chain}")
            print(response.text)            
            return None

        contract_name = response.json()['result'][0]['ContractName']
        if not contract_name:
            print(f"No contract/name associated with address {address}")
            return None
        
        print(f"{chain}: {address} -> {contract_name}")
        time.sleep(sleep)
        return contract_name    
    except:
        print(f"\n\n** Fatal error looking up a contract at address {address}\n\n")
        return None


def parse_csv(csv_path, address_col, label_col, chain):

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    for row in rows:
        address = row[address_col]
        label = row[label_col]
        if address[:2] != '0x':
            continue

        address_type = "eoa" if is_eoa(chain, address, sleep=0) else "contract"
        contract_name = fetch_contract_name(chain, address, sleep=0) if address_type == "contract" else None
        if isinstance(contract_name, str):
            contract_name = contract_name.lower()

        if 'wallet' in label:
            if address_type == 'eoa':
                row[label_col] = 'eoa wallet'
            elif isinstance(contract_name, str) and 'safe' in contract_name:
                row[label_col] = 'safe wallet'
            else:
                row[label_col] = 'unknown wallet'
        elif 'contract' in label:
            if address_type == 'contract':
                if isinstance(contract_name,str) and 'factory' in contract_name:
                    row[label_col] = 'factory contract'
                else:
                    row[label_col] = 'contract'
            elif address_type == 'eoa':
                row[label_col] = 'eoa'
    
    with open(csv_path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)