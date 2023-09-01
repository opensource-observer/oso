import argparse
from dotenv import load_dotenv
import os
import requests


load_dotenv()
API_KEY = os.getenv("ETHERSCAN_API_KEY")

CHAINS = {
    'optimism': 'https://api-optimistic.etherscan.io/api',
    'mainnet': 'https://api.etherscan.io/api' 
}

def fetch_contract_info(chain, address):    
    api_url = CHAINS[chain]
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': address,
        'apikey': API_KEY
    }
    response = requests.get(api_url, params=params)
    if response.json()['status'] != '1':
        print(f"Error looking up a contract at address {address}")
        return None

    contract_name = response.json()['result'][0]['ContractName']
    if not contract_name:
        print(f"No contract/name associated with address {address}")
        return None
    
    print(f"{chain}: {address} -> {contract_name}")
    return contract_name    


parser = argparse.ArgumentParser(description='Fetch Ethereum contract info.')
parser.add_argument('chain', type=str, help='Blockchain chain (e.g., optimism, mainnet)')
parser.add_argument('address', type=str, help='Contract address')
args = parser.parse_args()
fetch_contract_info(args.chain, args.address)