import json
from fuzzywuzzy import fuzz, process

from address_tagging import is_eoa, fetch_contract_name
from ossd import (
    get_yaml_data_from_path, 
    map_addresses_to_slugs, 
    map_repos_to_slugs, 
    map_slugs_to_names, 
    map_slugs_to_project_data
)



GOVGRANTS_DATA_PATH = "data/govgrants/Optimism_GovFund_PublicTracker.json"

def load_grants_data():
    with open(GOVGRANTS_DATA_PATH) as f:
        grants_data = json.load(f)
    
    if not any("Address Tags" in grant for grant in grants_data):
        tag_grant_addresses()
        grants_data = load_grants_data()

    return grants_data


def tag_grant_addresses():
    
    grants = load_grants_data()
    for grant in grants:        
        address = grant['Address'].lower()
        if address[:2] != "0x":
            continue
        if " " in address:
            print(f"Splitting address for {grant['Project Name']} to {address}") 
            address = address.split(" ")[0]
        grant.update({"Address": address})             

        if is_eoa('optimism', address):
            grant.update({"Address Tags": ["eoa", "wallet"]})
        else:
            contract_name = fetch_contract_name('optimism', address)  
            if not isinstance(contract_name, str):
                print(f"Found unknown contract at {address}.")
                grant.update({"Address Tags": ["wallet"]})
            elif "Proxy" in contract_name or "MultiSig" in contract_name:
                grant.update({"Address Tags": ["safe", "wallet"]})
            else:
                print(f"Found other contract type at {address}: {contract_name}")
                grant.update({"Address Tags": ["wallet"]})
    
    with open(GOVGRANTS_DATA_PATH, "w") as f:
        json.dump(grants, f, indent=4)


def load_yaml_data():
    return get_yaml_data_from_path()


def find_closest_match(project_name, names_dict, num_matches=3):
    
    settings = dict(scorer=fuzz.token_set_ratio, limit=num_matches)
    names = list(names_dict.values())
    matches = process.extract(project_name, names, **settings)
    return matches
    

def parse_grants_data():

    grants_data = load_grants_data()
    yaml_data = load_yaml_data()

    addresses = map_addresses_to_slugs(yaml_data, chain='optimism')
    repos = map_repos_to_slugs(yaml_data)
    names = map_slugs_to_names(yaml_data)
    mapping = map_slugs_to_project_data(yaml_data)

    found_count = 0
    missing_addresses = []
    new_projects = {}
    for project in grants_data:
        name = project['Project Name']
        address = project['Address'].lower()
        if address[:2] != "0x":
            missing_addresses.append(name)
            continue
        if " " in address:
            print(f"Splitting address for {name} to {address}") 
            address = address.split(" ")[0]             
        if address in addresses:
            found_count += 1
            continue
        if address not in new_projects:
            matches = find_closest_match(name, names)
            print(f"Found no match for {name} at {address}. Closest matches: {matches}")
            new_projects[address] = []
        new_projects[address].append(name)

    #print(new_projects)
    print(f"Found {found_count} projects in OSSD.")
    print("New projects:", len(new_projects))
    

parse_grants_data()        


    

