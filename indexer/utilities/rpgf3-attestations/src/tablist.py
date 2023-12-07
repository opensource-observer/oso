import json
import os
import pandas as pd
import requests


START_TIME       = 	1699246800 # 6 Nov 2023 00:00:00
VOTERS_SCHEMA    = "0xfdcfdad2dbe7489e0ce56b260348b7f14e8365a8a325aef9834818c00d46b31b"
LIST_SCHEMA      = "0x3e3e2172aebb902cf7aa6e1820809c5b469af139e7a4265442b1c22b97c6b2a5"
DATA_EXPORT_JSON = "data/list_data.json"
DATA_EXPORT_CSV  = "data/list_data.csv"


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


def dump_json(data, path):
    path = f"data/lists/{path}.json"
    with open(path, "w") as json_file:
        json.dump(data, json_file, indent=4)


def request_json_data(attestations):
    """
    Request and insert the JSON data for each attestation.
    """

    for a in attestations:
        url = a["data"][2]["value"]["value"]
        gateway = "https://cloudflare-ipfs.com"
        if isinstance(url, str):
            url = url.replace("https://w3s.link", gateway)
            if "https://" not in url:
                url = f"{gateway}/ipfs/{url}"
            print(url)
            json_data = fetch_json_data(url)
            if json_data:
                a.update({"json_data": json_data})
                dump_json(json_data, a["id"])


def generate_csv(voting_lists):
    csv_data = []
    for vlist in voting_lists:
        list_id = vlist['id']
        attester = vlist['attester']
        list_name = vlist['data'][0]['value']['value']
        time_created = vlist['timeCreated']

        if 'json_data' not in vlist:
            print(f"Missing data for list {list_id}")
            continue
        allocations = {item['RPGF3_Application_UID']: item['OPAmount'] for item in vlist['json_data']['listContent']}
        
        impact_category = vlist['json_data']['impactCategory']
        if not isinstance(impact_category, list):
            continue
        series = pd.Series(allocations)
        stats = {
            "count": series.count(),
            "sum": series.sum(),
            "mean": series.mean(),
            "std": series.std(),
            "min": series.min(),
            "max": series.max()
        }
        csv_row = {
            'id': list_id,
            'attester': attester,
            'listName': list_name,
            'timeCreated': time_created,
            **stats,
            **allocations
        }
        csv_data.append(csv_row)
    df = pd.DataFrame(csv_data)
    return df


def main():

    voters_data = fetch_all_attestations(VOTERS_SCHEMA)
    voters = [v["recipient"] for v in voters_data]
    print(f"\nTotal valid voters: {len(voters)}")
    
    data = fetch_all_attestations(LIST_SCHEMA)
    data = [
        d for d in data
        if (
            d["attester"] in voters 
            and d["attester"] == d["recipient"]
            and d['timeCreated'] > START_TIME
        )
    ]   
    print(f"\nTotal valid lists: {len(data)}")

    print("\nRequesting JSON data for valid lists (this may take a minute)...")
    request_json_data(data)

    with open(DATA_EXPORT_JSON, "w") as json_file:
        json.dump(data, json_file, indent=4)
    print(f"\nExported data to {DATA_EXPORT_JSON}.")

    df = generate_csv(data)
    df.sort_values(by=['timeCreated'], inplace=True)
    df.set_index('id', inplace=True, drop=True)
    df.drop(['attester', 'timeCreated'], axis=1, inplace=True)
    df.T.to_csv(DATA_EXPORT_CSV)


if __name__ == "__main__":
    main()