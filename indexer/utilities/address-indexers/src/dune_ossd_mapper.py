import json
from collections import defaultdict

from ossd import get_yaml_data_from_path, update_yaml_data, assign_slugs_to_addresses

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
    yaml_addresses = assign_slugs_to_addresses(yaml_data, chain='optimism')
    
    # Parse Dune data
    dune_addresses, dune_duplicates = parse_dune_data(dune_data)
    
    # Initialize mappings
    mapping = {
        "one_to_one": {},
        "yaml_to_multiple_dune": defaultdict(list),
        "dune_to_multiple_yaml": defaultdict(list),
        "no_yaml": defaultdict(list),
        "no_dune": defaultdict(list),
        "dune_duplicates": dune_duplicates
    }
    
    # One to One and Multiple Dune to YAML
    for address, dune_name in dune_addresses.items():
        yaml_slug = yaml_addresses.get(address, None)
        if yaml_slug:
            if dune_name not in mapping["dune_to_multiple_yaml"]:
                mapping["one_to_one"][dune_name] = yaml_slug
            mapping["dune_to_multiple_yaml"][dune_name].append(yaml_slug)
    
    # Multiple YAML to Dune and No Dune
    for address, yaml_slug in yaml_addresses.items():
        dune_names = dune_data.get(address, {}).get("project_list", [])
        if dune_names:
            if len(dune_names) > 1:
                mapping["yaml_to_multiple_dune"][yaml_slug].extend(dune_names)
        else:
            mapping["no_dune"][yaml_slug].append(address)
            
    # No YAML
    for address, dune_info in dune_duplicates.items():
        for dune_name in dune_info['project_list']:
            if dune_name not in mapping["one_to_one"] and dune_name not in mapping["dune_to_multiple_yaml"]:
                mapping["no_yaml"][dune_name].append(address)
                
    # Convert defaultdict to dict for JSON serialization
    mapping = {key: dict(value) for key, value in mapping.items()}

    # De-duplicate and sort the lists in mappings
    for key in ["yaml_to_multiple_dune", "dune_to_multiple_yaml", "no_yaml", "no_dune"]:
        mapping[key] = {k: sorted(list(set(v))) for k, v in mapping[key].items()}
    
    # Identify Dune names that map to a single YAML slug to move them from 'dune_to_multiple_yaml' to 'one_to_one'
    keys_to_move = []
    for dune_name, yaml_slugs in mapping['dune_to_multiple_yaml'].items():
        if len(yaml_slugs) == 1:
            keys_to_move.append(dune_name)
            
    # Perform the move
    for key in keys_to_move:
        mapping['one_to_one'][key] = mapping['dune_to_multiple_yaml'][key][0]
        del mapping['dune_to_multiple_yaml'][key]
    
    # Sort the keys in each dictionary
    mapping = {key: dict(sorted(value.items())) for key, value in mapping.items()}

    # Sort the keys in the main mapping dictionary as well
    mapping = dict(sorted(mapping.items()))

    
    with open(MAPPING_FILE_PATH, "w") as f:
        json.dump(mapping, f, indent=4)


map_dune_names_to_yaml_slugs()



