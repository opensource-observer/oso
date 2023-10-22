import json
import os
import pandas as pd
import requests

from parse_links import Parser


EAS_SCHEMA = "0x76e98cce95f3ba992c2ee25cef25f756495147608a3da3aa2e5ca43109fe77cc"
START_TIME = 0
RAW_APPLICANT_JSON = "data/raw_applicant_data.json"
OSSD_SNAPSHOT_JSON = "data/ossd_snapshot.json"
CLEANED_APPLICANT_JSON = "data/cleaned_applicant_data.json"
CLEANED_APPLICANT_CSV = "data/cleaned_applicant_data.csv"


def fetch_attestations(schema_id, time_created_after=0):
  
    url = 'https://optimism.easscan.org/graphql'
    query_limit = 100

    query = '''
    query Attestations($schemaId: StringFilter!, $skip: Int!, $take: Int!, $timeCreatedAfter: IntFilter) {
        attestations(where: {schemaId: $schemaId, timeCreated: $timeCreatedAfter}, take: $take, skip: $skip) {
            id
            attester
            recipient
            refUID
            revocable
            revocationTime
            expirationTime
            timeCreated 
            decodedDataJson    
        }
    }
    '''
    
    variables = {
        "schemaId": {
            "equals": schema_id
        },
        "skip": 0,
        "take": query_limit,
        "timeCreatedAfter": {"gt": time_created_after},
    }

    headers = {
        'Content-Type': 'application/json',
    }

    all_attestations = []

    while True:
        payload = {
            'query': query,
            'variables': variables
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()

            data = response.json()
            attestations = data.get('data', {}).get('attestations', [])
            all_attestations.extend(attestations)

            if len(attestations) < query_limit:
                break

            variables["skip"] += query_limit

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Failed to fetch attestations for {schema_id}: {str(e)}")
            break

    print(f"Total attestations for Schema ID {schema_id}: {len(all_attestations)}")
    return all_attestations


def fetch_json_data(url):
 
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching JSON data from URL: {url}. Error: {str(e)}")
        return None


def fetch_and_update_json_data(data_entry):
 
    for data_item in data_entry:
        value = data_item.get("value", {}).get("value", {})
        if isinstance(value, str) and ".json" in value:
            json_data = fetch_json_data(value)
            if json_data:
                data_item.update({"json_data": json_data})


def update_data(schema_id, json_outpath):

    data = []
    last_time_created = 0

    if os.path.exists(json_outpath):
        with open(json_outpath, "r") as json_file:
            data = json.load(json_file)
        if len(data) > 0:
            last_time_created = max([a["timeCreated"] for a in data])
        else:
            last_time_created = START_TIME
    
    schema_attestations = fetch_attestations(schema_id, time_created_after=last_time_created)

    indexed_data = []
    for a in schema_attestations:
        decoded_data = json.loads(a["decodedDataJson"])
        fetch_and_update_json_data(decoded_data)
        indexed_data.append({
            "id": a["id"],
            "attester": a["attester"],
            "timeCreated": a["timeCreated"],
            "data": decoded_data
        })

    data.extend(indexed_data)

    with open(json_outpath, "w") as json_file:
        json.dump(data, json_file, indent=4)

    return data


def clean_data(original_data):

    try:
        project_name = original_data["data"][0]["value"]["value"]
        project_link = original_data["data"][2]["value"]["value"]
        json_data = original_data["data"][2].get("json_data", None)

        if json_data is None:
            print(f"No JSON data found for {project_name} at {project_link}.")
            return None

        transformed_data = {
            "Project Name": project_name,
            "Applicant Type": json_data["applicantType"],
            "Date": original_data["timeCreated"],
            "Attester Address": original_data["attester"],
            "Payout Address": json_data["payoutAddress"],
            "Link": project_link,
            "Tags": json_data["impactCategory"],
            "Contributions: Github": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "GITHUB_REPO" and "https://github.com/" in item["url"] and len(item["url"]) > 20],
            "Contributions: Contracts": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "CONTRACT_ADDRESS" and "0x" in item["url"]],
            "Contributions: Other": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "OTHER"],
            "Impact Metrics": [item["url"] for item in json_data["impactMetrics"]]
        }
        return transformed_data
    except KeyError:
        print(f"Error cleaning data: Missing key in original data.")
        return None


def check_for_ossd_membership(cleaned_data):

    with open(OSSD_SNAPSHOT_JSON, "r") as json_file:
        ossd_data = json.load(json_file)
    
    addresses_to_slugs = ossd_data["addresses"]
    repos_to_slugs = {repo.replace("https://github.com/",""): slug for repo,slug in ossd_data["repos"].items()}
    address_set = set(addresses_to_slugs.keys())

    for project in cleaned_data:
        
        project["OSS Directory"] = "Not Found"
        address_found = False
        github_found = False
        project["Slug(s)"] = []

        if project["Payout Address"].lower() in address_set:
            address_found = True
            project["Slug(s)"].append(addresses_to_slugs[project["Payout Address"].lower()])
        elif project["Attester Address"].lower() in address_set:
            address_found = True
            project["Slug(s)"].append(addresses_to_slugs[project["Attester Address"].lower()])
        else:
            for url in project["Contributions: Contracts"]:
                owner = Parser.etherscan(url)[1]
                if owner is None:
                    continue
                if owner in address_set:
                    address_found = True
                    project["Slug(s)"].append(addresses_to_slugs[owner])
                    
        for url in project["Contributions: Github"]:
            repo = Parser.github(url)[1]            
            if repo is None:
                continue
            owner = repo.split("/")[0] if "/" in repo else repo
            if repo in repos_to_slugs:
                github_found = True
                project["Slug(s)"].append(repos_to_slugs[repo])
            elif owner in repos_to_slugs:
                github_found = True
                project["Slug(s)"].append(repos_to_slugs[owner])                
            
                
        if address_found and github_found:
            project["OSS Directory"] = "Address & Github Found"
        elif address_found:
            project["OSS Directory"] = "Address Found"
        elif github_found:
            project["OSS Directory"] = "Github Found"
        else:
            continue

        project["Slug(s)"] = list(set(project["Slug(s)"]))


def export_cleaned_data(raw_data, json_outpath, csv_outpath):
    
    cleaned_data = [clean_data(data) for data in raw_data]
    cleaned_data = [data for data in cleaned_data if data is not None]

    check_for_ossd_membership(cleaned_data)

    with open(json_outpath, "w") as json_file:
        json.dump(cleaned_data, json_file, indent=4)

    for entry in cleaned_data:
        entry["Tags"] = ", ".join(entry["Tags"])
        entry["Github (First Link)"] = entry["Contributions: Github"][0] if len(entry["Contributions: Github"]) > 0 else ""

    csv_data = pd.DataFrame(cleaned_data)
    fieldnames = ["Project Name", "Applicant Type", "Date", "Attester Address", "Payout Address", "Link", "Tags", "Github (First Link)", "OSS Directory"]
    csv_data = csv_data[fieldnames]
    csv_data.sort_values(by="Date", inplace=True)
    csv_data.drop_duplicates(subset=["Link"], keep="last", inplace=True)
    csv_data.to_csv(csv_outpath, index=False)


def main():

    data = update_data(EAS_SCHEMA, RAW_APPLICANT_JSON)
    export_cleaned_data(data, CLEANED_APPLICANT_JSON, CLEANED_APPLICANT_CSV)
    

if __name__ == "__main__":
    main()
