import json
import pandas as pd
from urllib.parse import urlparse


JSON_ATTESTATION_DATA = "data/rpgf3/indexed_attestations.json"


def extract_website_name(url):

    if not url:
        return 'none'
    parsed_url = urlparse(url)
    domain_parts = parsed_url.netloc.split('.')
    domain = domain_parts[-2] if len(domain_parts) > 1 else parsed_url.netloc

    mapping = {
        "x": "twitter",
        "t": "telegram",
        "youtu": "youtube",
        "npmjs": "npm",
        "npm-stat": "npm"
    }

    return mapping.get(domain, domain)



def tidy_dataframe(data):

    print(f"Ingesting total of {len(data)} records.")

    records = []
    for record in data:

        # Basic information
        record_id = record['id']
        attester = record['attester']
        time_created = record['timeCreated']
        
        # Extract nested data
        json_data = {}
        for item in record['data']:
            if item['name'] == 'applicationMetadataPtr':
                application_metadata_ptr = item['value']['value']
                json_data = item.get('json_data', {})
                break
        
        # Applicant details
        name = next((item['value']['value'] for item in record['data'] if item['name'] == 'displayName'), None)
        applicant_type = json_data.get('applicantType', '')
        bio_or_description = json_data.get('bio', '')
        impact_categories = ', '.join(json_data.get('impactCategory', []))
        
        # Contribution Links
        for contribution in json_data.get('contributionLinks', []):
            records.append([record_id, attester, time_created, name, application_metadata_ptr, applicant_type, 
                            bio_or_description, impact_categories, 'contributionLink', contribution['url'], 
                            contribution['description'], ''])
        
        # Impact Metrics
        for impact_metric in json_data.get('impactMetrics', []):
            records.append([record_id, attester, time_created, name, application_metadata_ptr, applicant_type, 
                            bio_or_description, impact_categories, 'impactMetric', impact_metric['url'], 
                            impact_metric['description'], impact_metric['number']])
        
        # Funding Sources
        for funding_source in json_data.get('fundingSources', []):
            fs_url = funding_source.get('url', '')
            fs_description = f"{funding_source.get('type', '')} {funding_source.get('currency', '')}"
            fs_amount = funding_source.get('amount', '')
            records.append([record_id, attester, time_created, name, application_metadata_ptr, applicant_type, 
                            bio_or_description, impact_categories, 'fundingSource', fs_url, fs_description, fs_amount])

    # Create DataFrame
    df = pd.DataFrame(records, columns=['id', 'attester', 'timeCreated', 'name', 'applicationMetadataPtr', 
                                        'applicantType', 'bio or description', 'impactCategory(ies)', 
                                        'attestationType', 'attestationUrl', 'attestationDescription', 
                                        'number'])
    
    df['urlType'] = df['attestationUrl'].apply(extract_website_name)

    print(f"Created Tidy DataFrame with {len(df)} records.")
    return df


def main():

    with open(JSON_ATTESTATION_DATA, "r") as json_file:
        data = json.load(json_file)

    df = tidy_dataframe(data)
    csv_path = JSON_ATTESTATION_DATA.replace('.json', '.csv')
    df.to_csv(csv_path, index=False)


main()    