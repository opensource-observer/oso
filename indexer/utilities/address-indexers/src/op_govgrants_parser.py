import json
from fuzzywuzzy import fuzz, process

from address_tagging import is_eoa, fetch_contract_name
from ossd import (
    get_yaml_data_from_path, 
    map_addresses_to_slugs, 
    map_repos_to_slugs, 
    map_slugs_to_names, 
    map_slugs_to_project_data,
    update_yaml_data,
    make_template
)


GOVGRANTS_DATA_PATH = "data/govgrants/Optimism_GovFund_PublicTracker.json"

def load_grants_data():
    with open(GOVGRANTS_DATA_PATH) as f:
        grants_data = json.load(f)
    
    if not any("Address Tags" in grant for grant in grants_data):
        tag_grant_addresses(grants_data)

    return grants_data


def tag_grant_addresses(grants):
    
    for grant in grants:        
        if "Address Tags" in grant:
            continue
        
        # handle some special cases
        if address[0] == "x":
            address = "0" + address
        elif address == "noahlitvin.eth":
            address = "0x07Aeeb7E544A070a2553e142828fb30c214a1F86"
        
        address = grant['Address'].lower().strip()
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


def find_closest_match(project_name, names_dict, max_matches=10, fuzz_threshold=80):

    settings = dict(scorer=fuzz.token_set_ratio, limit=max_matches)
    names = list(names_dict.values())
    matches = process.extract(project_name, names, **settings)
    filtered_matches = [(name, score) for name, score in matches if score >= fuzz_threshold]
    matches_dict = {name: [k for k, v in names_dict.items() if v == name] for name, _ in filtered_matches}    
    return matches_dict


def parse_grants_data(last_slug=None):

    grants_data = load_grants_data()
    yaml_data = get_yaml_data_from_path()
    template = make_template(yaml_data)

    addresses = map_addresses_to_slugs(yaml_data, chain='optimism')
    repos = map_repos_to_slugs(yaml_data)
    names = map_slugs_to_names(yaml_data)
    mapping = map_slugs_to_project_data(yaml_data)

    slug_found = (last_slug is None)
    for project in grants_data:
        
        name = project['Project Name']
        address = project['Address']

        if last_slug and addresses.get(address, None) == last_slug:
            slug_found = True
        elif not slug_found:
            continue

        # case 1: grant address is already in YAML, confirm it has the right tags
        slug = addresses.get(address, None)
        if slug:
            print(f"Found {name}'s address at {slug} in OSSD.")
            update = False
            data = mapping[slug]            
            for addr in data['blockchain']:
                if addr['address'] == address:
                    if 'optimism' not in addr['networks']:
                        addr['networks'].append('optimism')
                        update = True
                    if set(project['Address Tags']) != set(addr['tags']):
                        addr['tags'] = list(set(addr['tags'] + project['Address Tags']))
                        update = True
                    break
            if update:
                update_yaml_data([data])
            continue
                
        print(f"\nFound no existing project for {name} at {address}.")
        print(f"Here is the proposal link, FYI: {project['Link']}")
        
        # case 2: grant address is not in YAML, but there appears to be an existing project already
        potential_names = find_closest_match(name, names)
        if potential_names:
            print(f"Here are some similar-named projects and their slugs: {potential_names}")            
        else:
            print("There aren't any projects with similar names.")                    
        print("Enter a slug for the project if there's a good match:")
        slug = input()
        data = mapping.get(slug, None)
        if data:
            data['blockchain'].append(
                {
                    "address": address,
                    "networks": ["optimism"],
                    "tags": project['Address Tags']
                }
            )
            update_yaml_data([data])
            continue
        
        # case 3: grant address is not in YAML, check if a new project needs to be created
        print("Do you want to create a new project? (y/n/q)")
        status = input()
        if status.lower() == 'q':
            return False
        elif status.lower() != 'y':
            continue        
        
        print("Enter a GitHub repo url for the project:")
        repo = input()
        if repos.get(repo, None):
            print(f"Found {repo} in OSSD.")
            data = mapping[repos[repo]]
            data['blockchain'].append(
                {
                    "address": address,
                    "networks": ["optimism"],
                    "tags": project['Address Tags']
                }
            )
            update_yaml_data([data])
            continue

        if repo:
            data = template.copy()
            data['github'] = [{"url": repo}]
            data['blockchain'] = [{
                "address": address,
                "networks": ["optimism"],
                "tags": project['Address Tags']
            }]
            slug = repo.split('/')[-1].lower()
            print(f"Would you like to use the slug {slug}? (y/n)")  
            status = input()
            if status.lower() == 'y':
                data['slug'] = slug
            else:
                print("Enter a slug for the project:")
                slug = input()
                data['slug'] = slug
            
            print(f"Would you like to use the name {name}? (y/n)") 
            status = input()
            if status.lower() == 'y':
                data['name'] = name
            else:
                print("Enter a name for the project:")
                name = input()
                data['name'] = name
            
            print(f"Would you like to export to a YAML file? (y/n/q)")
            status = input()
            if status.lower() == 'q':
                return False
            if status.lower() == 'y':
                update_yaml_data([data])
                continue
            else:
                continue


parse_grants_data()        