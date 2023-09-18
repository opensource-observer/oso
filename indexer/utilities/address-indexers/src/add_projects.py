import json
import yaml

from ossd import get_yaml_data_from_path, update_yaml_data



def load_data():
    """Load YAML and JSON data."""
    yaml_data = get_yaml_data_from_path()

    with open("data/allo/oss-projects.json") as f:
        new_data = json.load(f)

    return yaml_data, new_data


def create_slug_mapping(yaml_data):
    """Create a mapping from slug to project data and from GitHub URLs to slugs."""
    mapping = {}
    github_to_slug = {}

    for project in yaml_data:
        slug = project['slug']
        mapping[slug] = project

        github_urls = project.get('github', [])
        for url in github_urls:
            github_to_slug[url['url'].lower()] = slug

    return mapping, github_to_slug


def update_network_based_on_tags(addr):
    """Update the network for an address based on its tags."""
    unsupported_networks = ['pgn', 'fantom']

    for network in unsupported_networks:
        if network in addr['networks']:
            addr['networks'].remove(network)
            if 'eoa' in addr['tags']:
                addr['networks'].append('mainnet')

    if len(addr['networks']) == 0:
        return False # Indicate that the address should not be added
    return True  # Indicate that the address should be added


def update_project_blockchain_data(mapping, slug, project):
    """Update the blockchain data for a specific project."""
    
    new_address = [key for key in project.keys() if key not in ['name', 'github']][0]
    info = project[new_address]
    new_address = new_address.lower()

    updated = False
    for index, addr in enumerate(mapping[slug]['blockchain']):
        if addr['address'].lower() == new_address.lower():
            should_add = update_network_based_on_tags(addr)
            if should_add:
                # Update tags and networks only if they are different
                addr['tags'] = list(set(addr['tags']).union(set(info['tags'])))
                addr['networks'] = list(set(addr['networks']).union(set(info['networks'])))
                updated = True
            else:
                # Remove the address from the blockchain data
                del mapping[slug]['blockchain'][index]
            break

    if not updated:
        new_address_data = {
            "address": new_address,
            "tags": info['tags'],
            "networks": info['networks']
        }
        if update_network_based_on_tags(new_address_data):
            mapping[slug]['blockchain'].append(new_address_data)
            updated = True

    if updated:
        print(f"Updating {slug}")
        update_yaml_data([mapping[slug]])



def update_existing_projects(mapping, github_to_slug, new_data):
    """Check for new projects and update existing projects."""
    new_projects = []

    for project in new_data:
        github_info = project.get('github', {})
        if github_info:
            url = github_info.get('url', '').lower()
            slug = github_to_slug.get(url, None)

            if not slug:
                new_projects.append(project)
                continue

            if slug not in mapping or 'blockchain' not in mapping[slug]:
                continue

            update_project_blockchain_data(mapping, slug, project)

    return new_projects


def create_new_project(project, template):
    new_project = template.copy()
    addresses = [
        {"address": k, **v} 
        for k,v in project.items() 
        if k not in ['name', 'github']
    ]
    new_project['name'] = project['name']
    new_project['github'] = [project['github']]
    new_project['slug'] = project['github']['url'].split('/')[-1].lower()
    new_project['blockchain'] = addresses
    return new_project


def make_template(yaml_data):
    temp = yaml_data[0]
    template = {k: None for k in temp.keys()}
    template['version'] = temp.get('version', None)
    return template


def interactive_update(project_dict, template):
    
    project = create_new_project(project_dict, template)
    print("\nNew project:")
    print(project)
    print("\nDo you want to update this project? (y/n/q)")
    status = input()
    if status.lower() == 'q':
        return False
    elif status.lower() == 'n':
        return True
    elif status.lower() == 'yy':
        update_yaml_data([project])
        return True
    
    print("Enter a new name for the project:")
    name = input()
    if name:
        project['name'] = name
    
    print("Enter a new slug for the project:")
    slug = input()
    if slug:
        project['slug'] = slug
    
    print("\nDo you want to update this project? (y/n/q)")
    status = input()
    if status.lower() == 'q':
        return False
    elif status.lower() == 'y':
        update_yaml_data([project])
        return True
    else:
        return True


def make_collection_from_addresses(yaml_data, new_data, yaml_path, collection_name):
    
    address_to_slug_mapping = {}
    for project in yaml_data:
        addresses = project.get('blockchain', [])
        if not addresses:
            continue
        for addr in addresses:
            a = addr['address'].lower()
            address_to_slug_mapping[a] = project['slug']

    collection = []
    for project in new_data:
        for key in project.keys():
            if key not in ['name', 'github']:
                a = key.lower()
                slug = address_to_slug_mapping.get(a, None)
                if slug:
                    collection.append(slug)

    collection = sorted(list(set(collection)))    

    collection_data = {
        "version": 3,
        "slug": collection_name,
        "name": collection_name,        
        "projects": collection,
    }

    with open(yaml_path, 'w') as f:
        yaml.dump(collection_data, f)
    print("Dumped collection to", yaml_path)


def main():
    yaml_data, new_data = load_data()
    # mapping, github_to_slug = create_slug_mapping(yaml_data)

    # template = make_template(yaml_data)
    # new_projects = update_existing_projects(mapping, github_to_slug, new_data)
    # for project in new_projects:
    #     status = interactive_update(project, template)
    #     if status == False:
    #         break

    yaml_path = "data/allo/gitcoin-allo.yaml"
    collection_name = "gitcoin-allo"
    make_collection_from_addresses(yaml_data, new_data, yaml_path, collection_name)

if __name__ == "__main__":
    main()
