from dotenv import load_dotenv
import json
import os
import yaml

from parse_links import Parser

load_dotenv()
LOCAL_PATH = os.getenv("LOCAL_PATH_TO_OSSD")

OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"
DUPLICATE_SLUG_RESOLVER = {
    "bootnodedev": "0x7c96c745536a31712abeccc61dca77089e8eb9ab59876e5d40986700c834aca2",
    "filosofiacodigo": "0x74c9135b2ca59c277d93942e535f02777d2779f1fee5b88c9ff76ff20cdcd8b8",
    "gitcoin": "0x95bba9455fa1028d59c069660656b3fe0b46d7b2e1883b091c5b04b810bc7525", # Gitcoin and Passport
    "itu-blockchain": "0x956b110e3b9aa11c53bbf41b97d34fadb4d516faede3304fa2807db3fd6d7407", # OPClave & ITU
    "lxdao-official": "0x7d3cb52c6e006ca04df32b6bef1982962c0669a7b9d826114cf9f40c0ce9be97", # Various
    "metagov": "0x335ee234463e3a9bf9ea3325fd6942f30877714716b159ca7843f9b4d9ff4285", # MetaGov and DAOstar
    "playmint": "0x33135d1d7ea18427c5096af97f5d5bcac392b8bbe871a9a0a9dd62ce651212df", # Client Side Proofs and Downstream
    "polynomial-protocol": "0x90ef634fad04d6ac2882db44d4a84f31c7f0621f3abd00efb067416e4ff1641c", # Optimitic Indexer & Polynomial Bytes
    "rainbow": "0x723da383185924834ea462c791d4e21dac5dedc94ba164bd37adc571ba5008ed", # Rainbow Kit and Rainbow Me
    "reth-paradigmxyz": "0x62aa2cbedbc3772d3110b0927f0eea6313a71c9b3d7980ee631ca9aa2e9db3c6", # OP Reth
    "synapse": "0x224aae62a450603d6358ab1d699a3daeef169761279597712b08b8dc4d25b198", # Synapse Labs and Synapse DAO
    "ultrasoundmoney": "0xd06423aa05a359735b911e9988486822acb3c3f62e3397ed35d6430240454b0f", # Ultra Sound Money and Relay
    "vyperlang": "0x1b205ded96fa08412a2c8b7100de978779b13fd81fd8a85aaf71f7994065c690", # Vyper, Venom & Fang, Titanoboa
    "waffle-truefieng": "0xf162490ee7fc0844a9f2033eb1107cf910df56889ce42a28ea4bf049ae75bf63" # Waffle and Vaults.fyi
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