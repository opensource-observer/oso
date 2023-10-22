from dotenv import load_dotenv
import json
import os
import yaml


load_dotenv()
LOCAL_PATH = os.getenv("LOCAL_PATH_TO_OSSD")

OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"


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


def map_repos_to_slugs(yaml_data, lowercase=True):
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
                if lowercase:
                    url = url.lower()
                repos[url] = slug
    return repos


def main():

    yaml_data = get_yaml_data_from_path()
    addresses = map_addresses_to_slugs(yaml_data, chain='optimism')
    repos = map_repos_to_slugs(yaml_data)
    
    with open(OSSD_SNAPSHOT_JSON, 'w') as outfile:
        json.dump({
            'addresses': addresses,
            'repos': repos
        }, outfile, indent=4)


if __name__ == "__main__":
    main()