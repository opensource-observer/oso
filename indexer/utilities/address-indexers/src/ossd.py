from dotenv import load_dotenv
import os
import yaml
from yaml_formatter import dump


load_dotenv()
LOCAL_PATH = os.getenv("LOCAL_PATH_TO_OSSD")


def get_yaml_files(path):
    yaml_files = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".yaml"):
                yaml_files.append(os.path.join(root, file))
    return yaml_files


def get_yaml_data(yaml_files):
    yaml_data = []
    for file in yaml_files:
        with open(file, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
                if data:
                    yaml_data.append(data)
            except yaml.YAMLError as exc:
                print(f"Error in {file}: {exc}")
    return yaml_data


def get_yaml_data_from_path():
    yaml_files = get_yaml_files(LOCAL_PATH)
    if not yaml_files:
        print("No YAML files found.")
        return []
        
    print(f"Found {len(yaml_files)} yaml files.")
    yaml_data = get_yaml_data(yaml_files)
    print(f"Ingested {len(yaml_data)} yaml records.")
    return yaml_data


def update_yaml_data(yaml_data):
    print(f"Exporting {len(yaml_data)} yaml records to {LOCAL_PATH}.")
    for data in yaml_data:
        if not data:
            continue
        slug = data['slug']
        path = os.path.join(LOCAL_PATH, slug[0], slug + ".yaml")        
        dump(data, path)


def map_addresses_to_slugs(yaml_data, chain, lowercase=True):
    """
    Returns a mapping of addresses to slugs.
    Example:
    {
        "0x1234...": "project-slug"
    }
    """
    addresses = {}
    for data in yaml_data:
        if not data:
            continue
        slug = data['slug']
        blockchain_entries = data.get('blockchain', [])
        if not blockchain_entries:
            continue
        for entry in blockchain_entries:
            if chain not in entry.get('networks', []):
                continue
            address = entry.get('address', None)
            if address:
                if lowercase:
                    address = address.lower()
                addresses[address] = slug
    return addresses


def map_repos_to_slugs(yaml_data):
    """
    Returns a mapping of github repo urls to slugs.
    Example:
    {
        "https://github.com/my-repo": "project-slug"
    }
    """
    repos = {}
    for data in yaml_data:
        if not data:
            continue
        slug = data['slug']
        repo_entries = data.get('github', [])
        if not repo_entries:
            continue
        for entry in repo_entries:
            url = entry.get('url', None)
            if url:
                repos[url] = slug
    return repos


def map_slugs_to_names(yaml_data):
    """
    Returns a mapping of slugs to names.
    Example:
    {
        "project-slug": "My Project"
    }
    """
    mapping = {}
    for data in yaml_data:
        if not data:
            continue
        slug = data['slug']
        name = data['name']
        mapping[slug] = name
    return mapping


def map_slugs_to_project_data(yaml_data):
    """
    Returns a mapping of slugs to project data.
    Example:
    {
        "project-slug": {
            "name": "My Project",
            "github": "https://github.com/my-repo"
        }
    }
    """
    mapping = {}
    for data in yaml_data:
        if not data:
            continue
        slug = data['slug']
        mapping[slug] = data
    return mapping


def make_template(yaml_data):
    temp = yaml_data[0]
    template = {
        k: [] if isinstance(v, list) else None
        for k,v in temp.items()
    }
    template['version'] = temp.get('version', None)
    return template


def test():
    yaml_data = get_yaml_data_from_path()
    #update_yaml_data(yaml_data)
    addresses = map_addresses_to_slugs(yaml_data, chain='optimism')
    repos = map_repos_to_slugs(yaml_data)
    names = map_slugs_to_names(yaml_data)
    mapping = map_slugs_to_project_data(yaml_data)
    template = make_template(yaml_data)
    print("YAML template:")
    print(template)


#test()