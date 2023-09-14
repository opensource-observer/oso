import json

from ossd import get_yaml_data_from_path, update_yaml_data  


YAML_DATA = get_yaml_data_from_path()    

MAPPING_FILE_PATH = "data/dune_exports/mapping.json"
with open(MAPPING_FILE_PATH) as f:
    MAPPINGS = json.load(f)

DUNE_ADDRESS_DATA_PATH = "data/dune_exports/addresses.json"
with open(DUNE_ADDRESS_DATA_PATH) as f:
    DUNE_DATA = json.load(f) 

PROGRESS_FILE = "data/dune_exports/progress.txt"
def read_progress_from_file():
    try:
        with open(PROGRESS_FILE, "r") as f:
            return set(line.strip() for line in f.readlines())
    except FileNotFoundError:
        return set()

def save_progress_to_file(slug):
    with open(PROGRESS_FILE, "a") as f:
        f.write(f"{slug}\n")


def update_tags(addr):
    print(f"Current tags: {addr['tags']}")
    valid_tags = ['eoa', 'contract', 'factory', 'creator']
    print("Enter new tags separated by a comma. Options include: eoa, contract, factory, creator")
    new_tags = input().split(',')
    
    while any(tag not in valid_tags for tag in new_tags):
        print("Invalid tags. Please try again.")
        new_tags = input().split(',')
    
    addr['tags'] = new_tags

def update_project_info(project, chain):

    for address, info in DUNE_DATA.items():
        if len(info['project_list']) > 1:
            continue

        project_name = info['project_list'][0]
        slug = MAPPINGS.get(project_name, None)
        if slug != project['slug']:
            continue

        address = address.lower()
        entry = {
            "address": address,
            "tags": info['tags'],
            "updated": True
        }
        if info.get('name'):
            entry['name'] = info.get('name')
        
        found = False
        for addr in project[chain]:
            if addr['address'] == address:
                addr.update(entry)
                found = True
                break
        if not found:
            project[chain].append(entry)

def interactive_update(project, chain):

    if chain not in project:
        return False

    updated_addresses = [addr for addr in project[chain] if 'updated' in addr]
    missed_addresses = [addr for addr in project[chain] if 'updated' not in addr]

    if updated_addresses:
        print(f"{project['slug']} updated {len(updated_addresses)} addresses.")

    if missed_addresses:
        print(f"{project['slug']} missed {len(missed_addresses)} addresses.")
        print("Do you want to update this project? (y/n/q)")
        status = input()
        if status.lower() == 'q':
            return 'quit'
        if status.lower() == 'n':            
            return False
        for addr in missed_addresses:
            print(f"Delete {addr['address']}? (y/n)")
            status = input()
            if status.lower() == 'y':
                project[chain].remove(addr)
            elif status.lower() == 'n':
                print(f"Update tags for {addr['address']}? (y/n)")
                status = input()
                if status.lower() == 'y':
                    update_tags(addr)            

    status = input("Do you want to update the project data? (y/n/q) ")
    if status == 'y':
        for addr in updated_addresses:
            del addr['updated']
        return True
        
    if status == 'q':
        return 'quit'

    return False


def main():
    
    chain = 'optimism'
    completed_slugs = read_progress_from_file()

    for project in YAML_DATA:
        update_project_info(project, chain)
    
    for project in YAML_DATA:
        if project['slug'] in completed_slugs:
            continue
        if project['slug'] not in MAPPINGS.values():
            continue
        
        status = interactive_update(project, chain)
        if status == 'quit':
            break
        elif status:
            update_yaml_data([project])
            save_progress_to_file(project['slug'])


if __name__ == "__main__":
    main()
