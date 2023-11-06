import json
import os
import pandas as pd
import requests

from oss_directory import check_for_ossd_membership


EAS_SCHEMA = "0x76e98cce95f3ba992c2ee25cef25f756495147608a3da3aa2e5ca43109fe77cc"
APPROVAL_SCHEMA = "0xebbf697d5d3ca4b53579917ffc3597fb8d1a85b8c6ca10ec10039709903b9277"
APPROVER_ADDRESS = "0x621477dBA416E12df7FF0d48E14c4D20DC85D7D9"
START_TIME = 0
END_TIME = 1698136205
RAW_APPLICANT_JSON = "data/raw_applicant_data.json"
CLEANED_APPLICANT_JSON = "data/cleaned_applicant_data.json"
CLEANED_APPLICANT_CSV = "data/cleaned_applicant_data.csv"
PROJECT_OSSD_MAPPINGS = "data/rpgf3_ossd_mappings.csv"


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
        if a["timeCreated"] > last_time_created:
            continue
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
            "Project ID": original_data["id"],
            "Project Name": project_name,
            "Applicant Type": json_data["applicantType"],
            "Date": original_data["timeCreated"],
            "Attester Address": original_data["attester"],
            "Payout Address": json_data["payoutAddress"],
            "Link": project_link,
            "Tags": json_data["impactCategory"],
            "Contributions: Github": [item["url"].strip("/") for item in json_data["contributionLinks"] if item["type"] == "GITHUB_REPO" and "https://github.com/" in item["url"] and len(item["url"]) > 20],
            "Contributions: Contracts": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "CONTRACT_ADDRESS" and "0x" in item["url"]],
            "Contributions: Other": [item["url"] for item in json_data["contributionLinks"] if item["type"] == "OTHER"],
            "Impact Metrics": [item["url"] for item in json_data["impactMetrics"]]
        }
        return transformed_data
    except KeyError:
        print(f"Error cleaning data: Missing key in original data.")
        return None


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)
    

def export_cleaned_data(raw_data, json_outpath, csv_outpath):
    
    cleaned_data = [clean_data(data) for data in raw_data]
    cleaned_data = [data for data in cleaned_data if data is not None]

    check_for_ossd_membership(cleaned_data)

    with open(json_outpath, "w") as json_file:
        json.dump(cleaned_data, json_file, indent=4, cls=SetEncoder)

    for entry in cleaned_data:
        entry["Tags"] = ", ".join(entry["Tags"])
        entry["Github (First Link)"] = entry["Contributions: Github"][0] if len(entry["Contributions: Github"]) > 0 else ""

    csv_data = pd.DataFrame(cleaned_data)
    fieldnames = ["Project Name", "Applicant Type", "Date", "Attester Address", "Payout Address", "Link", "Tags", "Github (First Link)", "OSS Directory"]
    csv_data = csv_data[fieldnames]
    csv_data.sort_values(by="Date", inplace=True)
    csv_data.drop_duplicates(subset=["Link"], keep="last", inplace=True)
    csv_data.to_csv(csv_outpath, index=False)

    return cleaned_data


def export_canonical_projects_list(cleaned_data, csv_outpath):    

    csv_data = pd.DataFrame(cleaned_data)
    cols = ["Project ID", "Project Name", "Slug: Primary", "Payout Address", "Slugs: Github", 
            "Slugs: Contract Address", "Slugs: Attester Address", "Slugs: Payout Address", "Contributions: Github"]
    csv_data = csv_data[cols]    
    csv_data.sort_values(by=["Slug: Primary", "Payout Address"], inplace=True)

    sep = " | "
    csv_data["Slugs: Github"] = csv_data["Slugs: Github"].apply(lambda x: sep.join(x))
    csv_data["Slugs: Contract Address"] = csv_data["Slugs: Contract Address"].apply(lambda x: sep.join(x))
    csv_data["Slugs: Attester Address"] = csv_data["Slugs: Attester Address"].apply(lambda x: sep.join(x))
    csv_data["Slugs: Payout Address"] = csv_data["Slugs: Payout Address"].apply(lambda x: sep.join(x))

    csv_data.loc[csv_data["Slugs: Github"] != "", "Contributions: Github"] = None

    csv_data.to_csv(csv_outpath, index=False)


def fetch_approved_project_ids():

    approved_projects = fetch_attestations(APPROVAL_SCHEMA)
    approved_project_ids = []
    rejected_project_ids = []
    for a in approved_projects:
        if a["attester"] != APPROVER_ADDRESS:
            continue
        data = json.loads(a["decodedDataJson"])
        if data[0]['value']['value'] == True:
            approved_project_ids.append(a["refUID"])
        else:
            print("Rejected:", a["refUID"])
            rejected_project_ids.append(a["refUID"])
            

    for rejected_id in rejected_project_ids:        
        if rejected_id in approved_project_ids:
            approved_project_ids.remove(rejected_id)
    return approved_project_ids


def main():

    print("Fetching project applications from EAS...")
    data = update_data(EAS_SCHEMA, RAW_APPLICANT_JSON)
    print("Dumped raw application data to:", RAW_APPLICANT_JSON)
    print()
    print("Fetching project approvals from EAS...")
    approved_project_ids = fetch_approved_project_ids()
    approved_data = [project for project in data if project["id"] in approved_project_ids]
    print(f"Found {len(approved_data)} approved projects.")
    print()
    print("Cleaning application data...")
    cleaned_data = export_cleaned_data(approved_data, CLEANED_APPLICANT_JSON, CLEANED_APPLICANT_CSV)
    print("Export cleaned application data to:", CLEANED_APPLICANT_JSON)
    print()
    print("Generating a list of projects in OSS Directory...")
    export_canonical_projects_list(cleaned_data, PROJECT_OSSD_MAPPINGS)
    print("Exported projects list to:", PROJECT_OSSD_MAPPINGS)
    

if __name__ == "__main__":
    main()
