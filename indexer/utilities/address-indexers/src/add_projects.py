import json
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

    if len(addr['networks']) == 0:
        return False # Indicate that the address should not be added
    return True  # Indicate that the address should be added


def update_project_blockchain_data(mapping, slug, project):
    """Update the blockchain data for a specific project."""
    
    new_address = [key for key in project.keys() if key not in ['name', 'github']][0]
    info = project[new_address]
    new_address = new_address.lower()

    updated = False
    for addr in mapping[slug]['blockchain']:
        if addr['address'] == new_address:
            if update_network_based_on_tags(addr):
                addr['tags'].extend(info['tags'])
                addr['networks'].extend(info['networks'])                        
                updated = True
            break
        else:
            new_address_data = {
                "address": new_address,
                "tags": info['tags'],
                "networks": info['networks']
            }
            if update_network_based_on_tags(new_address_data):
                mapping[slug]['blockchain'].append(new_address_data)
                updated = True
            break
    if updated:
        print("Updating", slug)
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
    addresses = {k:v for k,v in project.items() if k not in ['name', 'github']}
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


def main():
    yaml_data, new_data = load_data()
    mapping, github_to_slug = create_slug_mapping(yaml_data)
    new_projects = update_existing_projects(mapping, github_to_slug, new_data)
    template = make_template(yaml_data)
    new_project = create_new_project(new_projects[0], template)
    #update_yaml_data([new_project])


if __name__ == "__main__":
    main()
