import argparse
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

def is_eoa(chain, address, sleep=.20):
    
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


def fetch_contract_name(chain, address, sleep=.20):    
    
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