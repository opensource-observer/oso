import json
from collections import defaultdict

from ossd import get_yaml_data_from_path, update_yaml_data, map_addresses_to_slugs

DUNE_ADDRESS_DATA_PATH = "data/dune_exports/addresses.json"
MAPPING_FILE_PATH = "data/dune_exports/dune_ossd_mapping.json"

def load_dune_data():
    with open(DUNE_ADDRESS_DATA_PATH) as f:
        return json.load(f)


def load_yaml_data():
    return get_yaml_data_from_path()


def parse_dune_data(dune_data):
    addresses = {}
    duplicates = {}
    for address, info in dune_data.items():
        if len(info['project_list']) == 1:
            addresses[address] = info['project_list'][0]
        else:
            duplicates[address] = {
                'name': info.get('name', None),
                'project_list': info['project_list']
            }
    return addresses, duplicates



def map_dune_names_to_yaml_slugs():
    
    yaml_data = get_yaml_data_from_path()
    dune_data = load_dune_data()
    
    # Assign slugs to addresses
    yaml_addresses = map_addresses_to_slugs(yaml_data, chain='optimism')
    
    # Parse Dune data
    dune_addresses, dune_duplicates = parse_dune_data(dune_data)

    dune_spells_to_slugs = {}
    unmapped_addresses = {}
    mapped_projects = {}
    unmapped_projects = {}
    for address, dune_name in dune_addresses.items():
        yaml_slug = yaml_addresses.get(address, None)
        if not yaml_slug:
            unmapped_addresses[address] = dune_name
            continue

        # Case 1: Addressed has been mapped to a YAML
        if dune_name not in dune_spells_to_slugs:
            dune_spells_to_slugs[dune_name] = yaml_slug
            mapped_projects[yaml_slug] = {
                "dune_names": [dune_name],
                "mapped_addresses": 1,
                "unmapped_addresses": []
            }
        else:
            if dune_name not in mapped_projects[yaml_slug]["dune_names"]:
                mapped_projects[yaml_slug]["dune_names"].append(dune_name)
            mapped_projects[yaml_slug]["mapped_addresses"] += 1
                
    for address, dune_name in unmapped_addresses.items():
        # Case 2: Address is used by multiple projects; skip it
        if address in dune_duplicates:
            continue
        # Case 3: Address belongs to a mapped project but has been mapped yet
        if dune_name in dune_spells_to_slugs:
            mapped_projects[dune_spells_to_slugs[dune_name]]["unmapped_addresses"].append(address)
            continue
        # Case 4: Address belongs to a project that has not been mapped to a YAML
        if dune_name not in unmapped_projects:
            unmapped_projects[dune_name] = [address]
        else:
            unmapped_projects[dune_name].append(address)

    mapping = {
        "dune_spells_to_slugs": dune_spells_to_slugs,
        "mapped_projects": mapped_projects,
        "unmapped_projects": unmapped_projects,
        "dune_duplicates": dune_duplicates
    }

    mapping = {key: dict(sorted(value.items())) for key, value in mapping.items()}
    
    with open(MAPPING_FILE_PATH, "w") as f:
        json.dump(mapping, f, indent=4)


map_dune_names_to_yaml_slugs()



