import json
import os
import pandas as pd
import requests


VOTERS_SCHEMA    = "0xfdcfdad2dbe7489e0ce56b260348b7f14e8365a8a325aef9834818c00d46b31b"
LIST_SCHEMA      = "0x3e3e2172aebb902cf7aa6e1820809c5b469af139e7a4265442b1c22b97c6b2a5"
DATA_EXPORT_JSON = "list_data.json"
DATA_EXPORT_CSV  = "list_data.csv"


def fetch_attestations(schema_id, time_created_after=0):
    """
    Generalized function to fetch attestations for a given schema ID.
    """

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
        "timeCreatedAfter": {
            "gt": time_created_after
        },
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


def fetch_all_attestations (app_schema_id):
    """
    Fetch all lists from EAS and decode the data.
    """

    lists = fetch_attestations(app_schema_id)
    list_data = []
    for lst in lists:
        if lst["revocationTime"]:
            continue
        decoded_data = json.loads(lst["decodedDataJson"])
        list_data.append({
            **lst,
            "data": decoded_data
        })
    return list_data
    

def fetch_json_data(url):
    """
    Fetch JSON data from a URL.
    """
 
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching JSON data from URL: {url}. Error: {str(e)}")
        return None


def request_json_data(attestations):
    """
    Request and insert the JSON data for each attestation.
    """

    for a in attestations:
        url = a["data"][2]["value"]["value"]
        if isinstance(url, str):
            url = url.replace("https://w3s.link", "https://ipfs.io")
            if "https://" not in url:
                url = f"https://ipfs.io/ipfs/{url}"
            print(url)
            json_data = fetch_json_data(url)
            if json_data:
                a.update({"json_data": json_data})


def generate_csv(voting_lists):
    csv_data = []
    for vlist in voting_lists:
        list_id = vlist['id']
        attester = vlist['attester']
        list_name = vlist['data'][0]['value']['value']
        list_metadata = {d['name']: d['value']['value'] for d in vlist['data']}
        list_description = vlist['json_data'].get('listDescription', 'None')
        impact_evaluation_link = vlist['json_data'].get('impactEvaluationLink', 'None')
        impact_evaluation_description = vlist['json_data'].get('impactEvaluationDescription', 'None')
        impact_category = vlist['json_data'].get('impactCategory', 'None')
        allocations = {item['RPGF3_Application_UID']: item['OPAmount'] for item in vlist['json_data']['listContent']}
        csv_row = {
            'id': list_id,
            'attester': attester,
            'listName': list_name,
            'listDescription': list_description,
            'impactEvaluationLink': impact_evaluation_link,
            'impactEvaluationDescription': impact_evaluation_description,
            'impactCategory': impact_category,
            **allocations
        }
        csv_data.append(csv_row)
    df = pd.DataFrame(csv_data)
    df.fillna('None', inplace=True)
    return df


def main():

    voters_data = fetch_all_attestations(VOTERS_SCHEMA)
    voters = [v["recipient"] for v in voters_data]
    print(f"\nTotal valid voters: {len(voters)}")
    
    data = fetch_all_attestations(LIST_SCHEMA)
    data = [d for d in data if d["attester"] in voters]
    print(f"\nTotal valid lists: {len(data)}")

    print("\nRequesting JSON data for valid lists (this may take a minute)...")
    request_json_data(data)

    with open(DATA_EXPORT_JSON, "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"\nExported data to {DATA_EXPORT_JSON}.")

    df = generate_csv(data)
    df.to_csv(DATA_EXPORT_CSV, index=False)


if __name__ == "__main__":
    main()