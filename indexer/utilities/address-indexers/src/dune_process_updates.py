"""
This script takes in a JSON of project:creator addresses and two CSV files from Dune Analytics.

The project:creator spellbook is maintained here: 
https://github.com/duneanalytics/spellbook/blob/main/models/contracts/optimism/contracts_optimism_contract_creator_address_list.sql

The CSVs are maintained here:
- https://dune.com/queries/3015427 [EOA deployed contracts]
- https://dune.com/queries/3015464 [Factory deployed contracts]

Once the data is ingested, it updates the OSS Directory YAML files.
"""

from collections import Counter
import json
import os
import pandas as pd

from address_tagging import is_eoa, fetch_contract_name
from ossd import get_yaml_data_from_path, map_addresses_to_slugs, map_slugs_to_project_data, update_yaml_data


def get_datestamp():
    return pd.to_datetime('today').strftime("%Y-%m-%d")


def sql_to_json_spellbook(directory):

    sql_file = [f for f in os.listdir(directory) if '.sql' in f][0]
    with open(os.path.join(directory, sql_file), 'r') as file:
        sql = file.read()

    addresses = {}
    found_values = False
    for line in sql.split('\n'):
        if 'values' in line:
            found_values = True
        if '(creator_address, contract_project)' in line:
            break
        if found_values and '0x' in line:
            line = line.replace(',(','').replace('),','').replace(')','').replace('(','')            
            address = line.split(',')[0].strip().lower()
            project = line.split(',')[1].split('--')[0].strip().replace("'",'')
            addresses[address] = project

    addresses = {k: v for k, v in sorted(addresses.items(), key=lambda item: item[1].lower())}
    
    datestamp = get_datestamp()
    with open(os.path.join(directory, f'{datestamp}_spellbook.json'), 'w') as outfile:
        json.dump(addresses, outfile, indent=4)


def get_latest_file(directory, filename):
    latest_file = max([f for f in os.listdir(directory) if filename in f])
    return os.path.join(directory, latest_file)


def consolidate_addresses(directory):
    
    mapping_path = get_latest_file(directory, 'mapping')
    creators_path = get_latest_file(directory, 'spellbook')
    contracts_path = get_latest_file(directory, 'contracts')
    factories_path = get_latest_file(directory, 'factories')

    with open(mapping_path, 'r') as file:
        mapping = json.load(file)
    
    
    with open(creators_path, 'r') as file:
        creators = json.load(file)
    
    contracts = pd.read_csv(contracts_path)
    factories = pd.read_csv(factories_path)

    addresses = {}    
    for project, slug in mapping.items():
        if slug not in addresses:
            addresses[slug] = {
                "creator_addresses": [],
                "contract_addresses": [],
                "factory_addresses": [],
                "duplicate_addresses": []
            }        
        
        creators_list = [k for k, v in creators.items() if v.lower() == project.lower()]
        factories_list = list(factories[factories['contract_project'].str.lower() == project.lower()]['contract_creator_if_factory'])
        contracts_list = list(contracts[contracts['contract_project'].str.lower() == project.lower()]['contract_address'])
                
        addresses[slug]['creator_addresses'].extend(creators_list)
        addresses[slug]['contract_addresses'].extend(contracts_list)
        addresses[slug]['factory_addresses'].extend(factories_list)

    addresses = {k: {k2: list(set(v2)) for k2, v2 in v.items()} for k, v in addresses.items()}

    for slug, info in addresses.items():
        for address in info['factory_addresses']:
            if address in info['contract_addresses']:
                addresses[slug]['contract_addresses'].remove(address)
            if address in info['creator_addresses']:
                addresses[slug]['creator_addresses'].remove(address)

    address_counter = Counter()
    for slug, info in addresses.items():
        for k, v in info.items():
            address_counter.update(v)
    
    for address, count in address_counter.items():
        if count > 1:
            for slug, info in addresses.items():
                if address in info['creator_addresses']:
                    addresses[slug]['creator_addresses'].remove(address)
                    addresses[slug]['duplicate_addresses'].append(address)
                if address in info['factory_addresses']:
                    addresses[slug]['factory_addresses'].remove(address)
                    addresses[slug]['duplicate_addresses'].append(address)        
                if address in info['contract_addresses']:
                    addresses[slug]['contract_addresses'].remove(address)
                    addresses[slug]['duplicate_addresses'].append(address)                    
        
    return addresses


def diff_against_previous_run(current_run_path, previous_run_path):
    
    new_spells = json.load(open(get_latest_file(current_run_path, 'spellbook'), 'r'))
    old_spells = json.load(open(get_latest_file(previous_run_path, 'spellbook'), 'r'))

    mapping_path = get_latest_file(current_run_path, 'mapping')
    with open(mapping_path, 'r') as file:
        mapping = json.load(file)
    mapping = {k.lower(): v.lower() for k, v in mapping.items()}

    new_projects = list(set(new_spells.values()) - set(old_spells.values()))
    deleted_projects = list(set(old_spells.values()) - set(new_spells.values()))
    moved_creator_addresses = []
    new_creator_addresses = []
    deleted_creator_addresses = []

    for address, project in new_spells.items():
        if address not in old_spells:
            new_creator_addresses.append({
                "address": address,
                "to": project,
                "toSlug": mapping.get(project.lower(), None),
            })
        elif old_spells[address] != project:
            moved_creator_addresses.append({
                "address": address,
                "from": old_spells[address],
                "to": project,
                "fromSlug": mapping.get(old_spells[address].lower(), None),
                "toSlug": mapping.get(project.lower(), None),
            })
    for address, project in old_spells.items():
        if address not in new_spells:
            deleted_creator_addresses.append({
                "address": address,
                "from": project,
                "fromSlug": mapping.get(project.lower(), None),
            })

    unmapped_projects = {}
    mapped_projects = list(k.lower() for k in mapping.keys())
    for project in set(new_spells.values()):
        if project.lower() not in mapped_projects:
            unmapped_projects[project] = len([v for v in new_spells.values() if v == project])
    unmapped_projects = {k: v for k, v in sorted(unmapped_projects.items(), key=lambda item: item[1], reverse=True)}

    datestamp = get_datestamp()
    diff = {
        "date": datestamp,
        "new_projects": sorted(new_projects),
        "deleted_projects": sorted(deleted_projects),
        "moved_creator_addresses": moved_creator_addresses,
        "new_creator_addresses": new_creator_addresses,
        "deleted_creator_addresses": deleted_creator_addresses,
        "unmapped_projects": unmapped_projects
    }
    
    diff_path = os.path.join(current_run_path, f'{datestamp}_diff.json')
    with open(os.path.join(diff_path), 'w') as outfile:
        json.dump(diff, outfile, indent=4)

    return diff_path


def process_updates(directory):

    yaml_data = get_yaml_data_from_path()
    addresses_to_slug = map_addresses_to_slugs(yaml_data, 'optimism')
    slugs_to_projects = map_slugs_to_project_data(yaml_data)

    dune_address_data = consolidate_addresses(directory)

    for slug, info in dune_address_data.items():

        if slug in ['safe-global', 'ethereum-attestation-service']:  
            continue
        project_yaml = slugs_to_projects.get(slug, None)
        if not project_yaml:
            print(f"Skipping {slug} because it's not in the YAML.")
            continue

        for address in info['creator_addresses']:
            if address not in addresses_to_slug:
                addresses_to_slug[address] = slug
                print(f"Adding {address} to {slug} because it's not in the YAML.")
                if not is_eoa('optimism', address):
                    print("Warning: address is not an EOA.")
                    tags = ["contract", "creator"]
                else:
                    tags = ["eoa", "creator"]
                project_yaml['blockchain'].append({
                    "address": address,
                    "networks": ["optimism"],
                    "tags": tags
                })
        for address in info['contract_addresses']:
            if address not in addresses_to_slug:
                addresses_to_slug[address] = slug
                print(f"Adding {address} to {slug} because it's not in the YAML.")
                name = fetch_contract_name('optimism', address)
                project_yaml['blockchain'].append({
                    "address": address,
                    "name": name,
                    "networks": ["optimism"],
                    "tags": ["contract"]
                })
        for address in info['factory_addresses']:
            if address not in addresses_to_slug:
                addresses_to_slug[address] = slug
                print(f"Adding FACTORY {address} to {slug} because it's not in the YAML.")
                name = fetch_contract_name('optimism', address)
                project_yaml['blockchain'].append({
                    "address": address,
                    "name": name,
                    "networks": ["optimism"],
                    "tags": ["contract", "factory"]
                })

        approved_entries = []
        for address_entry in project_yaml['blockchain']:
            address = address_entry['address']
            if 'optimism' not in address_entry['networks']:
                approved_entries.append(address_entry)
                continue
            if 'wallet' in address_entry['tags'] or 'safe' in address_entry['tags']:
                approved_entries.append(address_entry)
                continue
            if not (address in info['creator_addresses'] or address in info['contract_addresses'] or address in info['factory_addresses']):
                print(f"Removing {address} from {slug} because it's not in Dune.")
                continue                
            if address in info['creator_addresses'] and 'creator' in address_entry['tags']:
                approved_entries.append(address_entry)
                continue
            if address in info['factory_addresses'] and 'factory' in address_entry['tags']:
                approved_entries.append(address_entry)
                continue
            if address in info['contract_addresses'] and 'contract' in address_entry['tags']:
                if 'factory' in address_entry['tags']:
                    address_entry['tags'].remove('factory')
                approved_entries.append(address_entry)
                continue    
            print(f"Removing {address} from {slug} because it's not in Dune.")

        for entry in approved_entries:
            if entry.get('name', None) is None:
                entry.pop('name', None)

        project_yaml['blockchain'] = approved_entries
        update_yaml_data([project_yaml])
                

if __name__ == "__main__":

    # uncomment these lines to perform preprocessing
    #sql_to_json_spellbook('data/dune_exports/')
    #diff_against_previous_run('data/dune_exports/', 'data/dune_exports/archive/')
    # addresses = consolidate_addresses('data/dune_exports/')
    # with open('data/dune_exports/addresses.json', 'w') as outfile:
    #     json.dump(addresses, outfile, indent=4)    

    # update the YAML files
    process_updates('data/dune_exports/')
    
