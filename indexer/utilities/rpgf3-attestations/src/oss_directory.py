from dotenv import load_dotenv
import json
import os
import yaml

from parse_links import Parser

load_dotenv()
LOCAL_PATH = os.getenv("LOCAL_PATH_TO_OSSD")

OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"
DUPLICATE_SLUG_RESOLVER = {
    "bootnodedev": "0x31fa3f2b3ab4221bb89dd64e864339a6c59ab6658d91860e239e2491f4bb2435",
    "filosofiacodigo": "0xaa3b9caf85727a484ac82d25594adc78d68fef1291de82be680bf00436164741",
    "gitcoin": "0x60085a98f5c48d97a28d7b45d193f9a734d1704e257df91827459b09565e0e47", # Gitcoin and Passport
    "itu-blockchain": "0x0517a9d930d480d5478b6b173e54376cd03ec48d17574baadde2a6322560c7a7", # OPClave & ITU
    "lxdao-official": "0x79aaf24aab7a9cffbaffd2003b262aa452d31b5a07fb17c54021479284c564be", # Various
    "metagov": "0xe367584886bdb185038a466f6a8e5a4ad746ffef051507a311cae85ae11c7d5e", # MetaGov and DAOstar
    "playmint": "0x60e8b63d4c87c43409731ac1370379af9884f7239cf69b052fb36c14d121f736", # Client Side Proofs and Downstream
    "polynomial-protocol": "0x75815ccd858e6b97c6e8435e24ec66b1bc4d67c4775a81d4b49a8c58b62daf3f", # Optimitic Indexer & Polynomial Bytes
    "rainbow": "0xe9140c31f3a448f0f52124b3f9782f7947d698a686ceb20f77f60366670f3f8e", # Rainbow Kit and Rainbow Me
    "reth-paradigmxyz": "0x356900a8a5aa893d522dfcd67cc89f6472f8793ea8cf41088b47833ff1c16b5f", # OP Reth
    "synapse": "0x3d2fe07760753070d5f3fe44fb92923065c688b56f3069906d8eae4cc3867fb6", # Synapse Labs and Synapse DAO
    "ultrasoundmoney": "0x5e97794e6f3b8af9c3b97da269e51387e788cb4b3c609d708aaa668538ef1de2", # Ultra Sound Money and Relay
    "vyperlang": "0x023dfdedcfb50385c8c24fd86489a7f016633219c66583c71f154d7af99c6b51", # Vyper, Venom & Fang, Titanoboa
    "waffle-truefieng": "0x877ded44fae0833c412ef1b802419a7d6d9e668c6f92f1fb439dbbd40ca12b2d", # Waffle and Vaults.fyi
    "banklessdao": "0x023ec749b1a3ad4335595edad791b6dd5523a94817f53cba336060779471c3c8" # Bankless DAO and International Media Nodes
}


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
                    url = url.lower().strip('/')
                repos[url] = slug
    return repos


def check_for_ossd_membership(cleaned_data):
    
    with open(OSSD_SNAPSHOT_JSON, "r") as json_file:
        ossd_data = json.load(json_file)
    
    # TODO: handle this more elegantly
    github_slugs_to_ignore = ['op', 'spellbook-duneanalytics']
    repos_to_slugs = {
        repo.replace("https://github.com/",""): slug
        for repo,slug in ossd_data["repos"].items()
        if slug not in github_slugs_to_ignore
    }

    addresses_to_slugs = ossd_data["addresses"]
    address_set = set(addresses_to_slugs.keys())

    for project in cleaned_data:
        
        project["OSS Directory"] = "Not Found"
        address_found = False        
        contract_found = False
        github_found = False

        project["Slugs: Payout Address"] = set()
        project["Slugs: Attester Address"] = set()
        project["Slugs: Contract Address"] = set()
        project["Slugs: Github"] = set()
        project["Slug: Primary"]  = None

        if project["Payout Address"].lower() in address_set:
            address_found = True
            project["Slugs: Payout Address"].add(addresses_to_slugs[project["Payout Address"].lower()])
        
        if project["Attester Address"].lower() in address_set:
            address_found = True            
            project["Slugs: Attester Address"].add(addresses_to_slugs[project["Attester Address"].lower()])

        for url in project["Contributions: Contracts"]:
            owner = Parser.etherscan(url)[1]
            if owner is None:
                continue
            if owner in address_set:
                contract_found = True
                project["Slugs: Contract Address"].add(addresses_to_slugs[owner])
                    
        for url in project["Contributions: Github"]:
            repo = Parser.github(url)[1]            
            if repo is None:
                continue
            owner = repo.split("/")[0] if "/" in repo else repo
            if repo in repos_to_slugs:
                github_found = True
                project["Slugs: Github"].add(repos_to_slugs[repo])
            elif owner in repos_to_slugs:
                github_found = True
                project["Slugs: Github"].add(repos_to_slugs[owner])                
                        
        if address_found and github_found:
            project["OSS Directory"] = "Address & Github Found"
        elif address_found:
            project["OSS Directory"] = "Address Found"
        elif github_found:
            project["OSS Directory"] = "Github Found"
        else:
            continue

        intersection = project["Slugs: Payout Address"].intersection(project["Slugs: Github"])
        union = project["Slugs: Payout Address"].union(project["Slugs: Github"]).union(project["Slugs: Contract Address"])
        if len(intersection) == 1:
            project["Slug: Primary"] = list(intersection)[0]
        elif len(intersection) > 1:
            project["Slug: Primary"] = list(project["Slugs: Payout Address"])[0]
        elif len(project["Slugs: Github"]) == 1:
            project["Slug: Primary"] = list(project["Slugs: Github"])[0]
        elif len(union) >= 1 and project["OSS Directory"] == "Address Found":
            project["Slug: Primary"] = list(project["Slugs: Payout Address"])[0]
        
        if project["Slug: Primary"] in DUPLICATE_SLUG_RESOLVER:
            expected_id = DUPLICATE_SLUG_RESOLVER[project["Slug: Primary"]]
            if project["Project ID"] != expected_id:
                print(f"Duplicate: {project['Project ID']} referencing {project['Slug: Primary']}")
                project["Slug: Primary"] = None        


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