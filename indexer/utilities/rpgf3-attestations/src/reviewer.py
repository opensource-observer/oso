import json
import pandas as pd

from parse_links import Parser

CLEANED_APPLICANT_JSON = "data/cleaned_applicant_data.json"
OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"
OSSD_REVIEWER_CSV = "data/ossd_reviewer.csv"


GITHUB_BASE = "https://github.com/"
def normalize_github_url(url):
    return url.lower().replace(GITHUB_BASE, "").strip('/')


def review_data(must_have_github=True):

    cleaned_applicant_data = json.load(open(CLEANED_APPLICANT_JSON, 'r'))
    existing_data = json.load(open(OSSD_SNAPSHOT_JSON, 'r'))
    existing_data['repos'] = {normalize_github_url(k): v for k, v in existing_data['repos'].items()}

    records = []
    for project in cleaned_applicant_data:
        
        name = project['Project Name']
        slugs = project['Slug(s)']
        if not slugs:
            slug = None
        elif len(slugs) > 1:
            print(f"WARNING: {name} has multiple slugs: {slugs}")
            slug = " && ".join(slugs)
        else:
            slug = slugs[0]

        props = dict(
            name = name, 
            slug = slug,
            project_type = project['Applicant Type']            
        )
        
        githubs = project['Contributions: Github']
        if must_have_github and not githubs:
            continue

        for github in githubs:
            artifact = Parser.github(github)
            if artifact is None or artifact[1] is None:
                continue
        
            repo = artifact[1]
            owner = repo.split("/")[0] if "/" in repo else repo
            if repo in existing_data['repos'] or owner in existing_data['repos']:
                continue
            url = GITHUB_BASE + repo
            if owner != repo:
                records.append({**props, 'artifact': repo, 'type': 'github repo', 'url': url})
            else:
                records.append({**props, 'artifact': repo, 'type': 'github owner', 'url': url})  

        contracts = project['Contributions: Contracts']
        for contract in contracts:
            artifact = Parser.etherscan(contract)
            if artifact is None or artifact[1] is None:
                continue
            address = artifact[1].lower()
            if address in existing_data['addresses']:
                continue
            url = 'https://optimistic.etherscan.io/address/' + address
            records.append({**props, 'artifact': address, 'type': 'contract', 'url': url})
        
        address = project['Payout Address'].lower()
        url = 'https://optimistic.etherscan.io/address/' + address
        if address not in existing_data['addresses']:
            records.append({**props, 'artifact': address, 'type': 'wallet', 'url': url})

    df = pd.DataFrame(records)
    df = df.drop_duplicates(keep='first')
    df.sort_values(by=['slug', 'type', 'name', 'artifact'], inplace=True)
    df.to_csv(OSSD_REVIEWER_CSV, index=False)


if __name__ == "__main__":
    review_data()
