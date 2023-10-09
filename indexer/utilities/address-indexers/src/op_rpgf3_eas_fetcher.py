import csv
import json
import os
import requests


from ossd import get_yaml_data_from_path, map_addresses_to_slugs, map_repos_to_slugs


ATTESTATIONS = {
    "Optimist Profile": "0xac4c92fc5c7babed88f78a917cdbcdc1c496a8f4ab2d5b2ec29402736b2cf929",
    "RPGF3 Application": "0x76e98cce95f3ba992c2ee25cef25f756495147608a3da3aa2e5ca43109fe77cc",
}

JSON_ATTESTATION_DATA = "data/rpgf3/indexed_attestations.json"
JSON_APPLICANT_DATA = "data/rpgf3/applicant_data.json"
CSV_OUTPUT_PATH = "data/rpgf3/applicant_data.csv"

def fetch_attestations_for_schema(schema_id, schema_name, time_created_after=0):
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

        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            try:
                data = response.json()
                if 'data' in data and 'attestations' in data['data']:
                    attestations = data['data']['attestations']
                    if attestations is None:
                        break
                    all_attestations.extend(attestations)
                else:
                    print(f"Unexpected response structure: {data}")
                    break

                if len(attestations) < query_limit:
                    break

                variables["skip"] += query_limit
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response: {str(e)}")
                break
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)
            break

    print(f"Total attestations for {schema_name}: {len(all_attestations)}")
    return all_attestations


def fetch_json_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to fetch JSON data from URL: {url}")
            return None
    except Exception as e:
        print(f"Error fetching JSON data from URL: {url}. Error: {str(e)}")
        return None


def fetch_and_update_json_data(data_entry):
    for data_item in data_entry:
        value = data_item.get("value", {}).get("value", {})
        if isinstance(value, str) and ".json" in value:
            json_data = fetch_json_data(value)
            if json_data:
                data_item.update({"json_data": json_data})


def update_json_file(schema_name_to_index):

    existing_data = []
    last_time_created = 0
    if os.path.exists(JSON_ATTESTATION_DATA):
        with open(JSON_ATTESTATION_DATA, "r") as json_file:
            existing_data = json.load(json_file)
        last_time_created = max([a["timeCreated"] for a in existing_data])

    indexed_data = []

    if schema_name_to_index in ATTESTATIONS:
        schema_id = ATTESTATIONS[schema_name_to_index]
        schema_attestations = fetch_attestations_for_schema(schema_id, schema_name_to_index, time_created_after=last_time_created)

        for a in schema_attestations:
            decoded_data = json.loads(a["decodedDataJson"])
            fetch_and_update_json_data(decoded_data)
            indexed_data.append({
                "id": a["id"],
                "attester": a["attester"],
                "timeCreated": a["timeCreated"],
                "data": decoded_data
            })
    
    existing_data.extend(indexed_data)
    
    with open(JSON_ATTESTATION_DATA, "w") as json_file:
        json.dump(existing_data, json_file, indent=4)

# very brittle, but works for now
def clean_data(original_data):
    transformed_data = {
        "Project Name": original_data["data"][0]["value"]["value"],  # Extract "displayName"
        "Applicant Type": original_data["data"][2]["json_data"]["applicantType"],  # Extract "applicantType" from "applicationMetadataPtr"
        "Date": original_data["timeCreated"],  # Extract "timeCreated"
        "Attester Address": original_data["attester"],  # Extract "attester"
        "Payout Address": original_data["data"][2]["json_data"]["payoutAddress"],  # Extract "payoutAddress" from "applicationMetadataPtr"
        "Link": original_data["data"][2]["value"]["value"],  # Extract "applicationMetadataPtr"
        "Tags": original_data["data"][2]["json_data"]["impactCategory"],  # Extract "impactCategory" from "applicationMetadataPtr"
        "Github Urls": [item["url"] for item in original_data["data"][2]["json_data"]["contributionLinks"] if item["type"] == "GITHUB_REPO"]  # Extract "GITHUB_REPO" URLs from "contributionLinks" in "applicationMetadataPtr"
    }
    return transformed_data


def check_for_ossd_membership(cleaned_data):

    yaml_data = get_yaml_data_from_path()
    addresses_to_slugs = map_addresses_to_slugs(yaml_data, "optimism")
    repos_to_slugs = map_repos_to_slugs(yaml_data)

    get_owner = lambda url: url.replace("https://github.com/","").split("/")[0].lower()
    
    repo_owner_set = set([get_owner(repo) for repo in repos_to_slugs.keys()])
    address_set = set(addresses_to_slugs.keys())
    
    for entry in cleaned_data:        
        
        github_owners = set([get_owner(repo) for repo in entry['Github Urls'].split(", ")])
        github_verified = False
        if github_owners.intersection(repo_owner_set):
            github_verified = True
        
        address_verified = False
        if entry["Payout Address"].lower() in address_set or entry["Attester Address"].lower() in address_set:
            address_verified = True

        if github_verified and address_verified:
            entry["OSS Directory"] = "Address & Github Found"
        elif github_verified:
            entry["OSS Directory"] = "Github Found"
        elif address_verified:
            entry["OSS Directory"] = "Address Found"
        else:
            entry["OSS Directory"] = "Not Found"


def clean_applicant_data():
    with open(JSON_ATTESTATION_DATA, "r") as json_file:
        original_data = json.load(json_file)
    cleaned_data = [clean_data(data) for data in original_data]
    with open(JSON_APPLICANT_DATA, "w") as json_file:
        json.dump(cleaned_data, json_file, indent=4)
    
    for entry in cleaned_data:
        entry["Tags"] = ", ".join(entry["Tags"])
        entry["Github Urls"] = ", ".join(entry["Github Urls"])
        entry["OSS Directory"] = "Unknown"

    check_for_ossd_membership(cleaned_data)

    with open(CSV_OUTPUT_PATH, mode='w', newline='') as csv_file:
        fieldnames = ["Project Name", "Applicant Type", "Date", "Attester Address", "Payout Address", "Link", "Tags", "Github Urls", "OSS Directory"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_data)


def main():
    update_json_file("RPGF3 Application")
    clean_applicant_data()


if __name__ == "__main__":
    main()