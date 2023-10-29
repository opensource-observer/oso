import json
import pandas as pd

from parse_links import Parser
from address_lookup import is_eoa, fetch_contract_name


CLEANED_APPLICANT_JSON = "data/cleaned_applicant_data.json"
OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"
OSSD_REVIEWER_CSV = "data/ossd_reviewer.csv"

ETHERSCAN_BASE = "https://optimistic.etherscan.io/address/"
GITHUB_BASE = "https://github.com/"


def normalize_github_url(url):
    return url.lower().replace(GITHUB_BASE, "").strip('/')


def process_wallet(payout_address):
    
    result = {
        "artifact": payout_address,
        "type": ["wallet"],
        "status": "review",
        "artifact_name": "RPGF3 Payout Address"
    }
    if is_eoa('optimism', payout_address):
        result['type'].append('eoa')
        result['status'] = 'OK'
    else:
        contract_name = fetch_contract_name('optimism', payout_address)
        if contract_name is not None and 'safe' in contract_name.lower():
            result['type'].append('safe')
            result['status'] = 'OK'
    result['type'] = " ".join(result['type'])
    
    return result


def process_github(github_url):
    
    github_url = normalize_github_url(github_url)
    result = {
        "artifact": github_url,
        "type": "github",
        "status": "review",
        "artifact_name": "Github URL"
    }
    artifact = Parser.github(github_url)
    if artifact is not None and artifact[1] is not None:
        repo = artifact[1]
        result['artifact'] = GITHUB_BASE + repo
        result['status'] = "OK"
        
    return result


def process_contract(contract_url):

    result = {
        "artifact": contract_url,
        "type": "contract",
        "status": "review",
        "artifact_name": None,
    }
    artifact = Parser.etherscan(contract_url)
    if artifact is not None and artifact[1] is not None:
        address = artifact[1].lower()
        result['artifact'] = address
        if is_eoa('optimism', address):
            result['type'] = "eoa"
        else:
            contract_name = fetch_contract_name('optimism', address)
            if contract_name is not None:
                result['artifact_name'] = contract_name
                contract_name = contract_name.lower()
                if 'safe' in contract_name:
                    result['type'] = "safe"                    
                elif 'factory' in contract_name:
                    result['type'] = "contract factory"
                    result['status'] = "OK"
                else:
                    result['status'] = "OK"
            
    return result


def review_data():

    cleaned_applicant_data = json.load(open(CLEANED_APPLICANT_JSON, 'r'))
    existing_data = json.load(open(OSSD_SNAPSHOT_JSON, 'r'))
    existing_data['repos'] = {normalize_github_url(k): v for k, v in existing_data['repos'].items()}

    records = []
    for project in cleaned_applicant_data:
        
        name = project['Project Name']        
        project_type = project['Applicant Type']

        # TODO: handle individual projects
        if project_type == 'INDIVIDUAL':
            continue

        slugs = project['Slug(s)']
        if len(slugs) > 1:
            slug = " && ".join(slugs)
        elif not slugs:
            slug = None    
        else:
            slug = slugs[0]

        props = dict(name=name, slug=slug, project_type=project_type)

        payout_address = project['Payout Address'].lower()
        wallet = process_wallet(payout_address)
        if payout_address not in existing_data['addresses']:            
            records.append({**props, **wallet, "workflow": "new"})
        else:
            records.append({**props, **wallet, "workflow": "existing"})
        
        githubs = project['Contributions: Github']
        for github_url in githubs:
            github_artifact = process_github(github_url)
            if github_artifact['artifact'] not in existing_data['repos']:
                records.append({**props, **github_artifact, "workflow": "new"})
            else:
                records.append({**props, **github_artifact, "workflow": "existing"})

        contracts = project['Contributions: Contracts']
        for contract_url in contracts:
            if 'goerli' in contract_url or 'mirror' in contract_url:
                continue
            contract_artifact = process_contract(contract_url)
            if contract_artifact['artifact'] not in existing_data['addresses']:
                records.append({**props, **contract_artifact, "workflow": "new"})
            else:
                records.append({**props, **contract_artifact, "workflow": "existing"})

    df = pd.DataFrame(records)
    df.to_csv(OSSD_REVIEWER_CSV)


if __name__ == "__main__":
    review_data()
