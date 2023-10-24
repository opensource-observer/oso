import json
import pandas as pd
from urllib.parse import urlparse

from parse_links import Parser


RAW_APPLICANT_JSON = "data/raw_applicant_data.json"
TIDY_ATTESTATION_CSV = "data/tidy_attestations.csv"
PROJECT_SUMMARY_CSV = "data/project_attestation_summary.csv"


def extract_website_name(url):

    if not url:
        return 'none'
    parsed_url = urlparse(url.strip('/'))
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
        
    # Create DataFrame
    df = pd.DataFrame(records, columns=['id', 'attester', 'timeCreated', 'name', 'applicationMetadataPtr', 
                                        'applicantType', 'bio or description', 'impactCategory(ies)', 
                                        'attestationType', 'attestationUrl', 'attestationDescription', 
                                        'number'])
    
    # Extract artifact name from attestationUrl
    df['urlType'] = df['attestationUrl'].apply(extract_website_name)
    df['artifactInfo'] = None
    df['artifactInfo'].update(df[df['urlType'] == 'etherscan']['attestationUrl'].apply(Parser.etherscan))
    df['artifactInfo'].update(df[df['urlType'] == 'npm']['attestationUrl'].apply(Parser.npm))
    df['artifactInfo'].update(df[df['urlType'] == 'github']['attestationUrl'].apply(Parser.github))
    df['artifactInfo'].update(df[df['urlType'] == 'twitter']['attestationUrl'].apply(Parser.twitter))
    df['artifactInfo'].update(df[df['urlType'] == 'substack']['attestationUrl'].apply(Parser.substack))

    def create_clean_link(url_type, artifact_info):
        if artifact_info is None:
            return None
        artifact = artifact_info[1]
        if artifact is None:
            return None
        if url_type == 'etherscan':
            return f"https://optimistic.etherscan.io/address/{artifact}"
        if url_type == 'npm':
            return f"https://www.npmjs.com/package/{artifact}"
        if url_type == 'github':
            return f"https://github.com/{artifact}"
        if url_type == 'twitter':
            return f"https://x.com/{artifact}"
        if url_type == 'substack':
            return f"https://{artifact}.substack.com/"
    
    df['linkValidation'] = df['artifactInfo'].apply(lambda x: x[0].title() if x is not None else 'n/a')
    df['cleanArtifactLink'] = df.apply(lambda row: create_clean_link(row['urlType'], row['artifactInfo']), axis=1)

    df['potentialConflict'] = None
    for artifact in df['cleanArtifactLink'].unique():
        if artifact is None:
            continue
        artifact_attesters = df[df['cleanArtifactLink'] == artifact]['attester'].unique()        
        if len(artifact_attesters) > 1:
            names = df[df['cleanArtifactLink'] == artifact]['name'].unique()
            conflict = " & ".join([f"{name} ({attester})" for name, attester in zip(names, artifact_attesters)])
            df.loc[df['cleanArtifactLink'] == artifact, 'potentialConflict'] = conflict


    print(f"Created Tidy DataFrame with {len(df)} records.")
    return df


def project_summary(df):

    groupers = ['name', 'applicationMetadataPtr', 'applicantType', 'bio or description', 'impactCategory(ies)']
    grouped_df = df.groupby(groupers).agg(
        attestationCount=('id', 'count'),
        contributionLinkCount=('attestationType', lambda x: (x == 'contributionLink').sum()),
        impactMetricCount=('attestationType', lambda x: (x == 'impactMetric').sum()),
        cleanArtifactLinkCount=('cleanArtifactLink', lambda x: x.notnull().sum()),
        potentialConflictCount=('potentialConflict', lambda x: x.notnull().sum()),
        urlTypeCount=('urlType', lambda x: x.value_counts().to_dict())
    ).reset_index()

    return grouped_df
        
def main():

    with open(RAW_APPLICANT_JSON, "r") as json_file:
        data = json.load(json_file)

    df = tidy_dataframe(data)
    df.to_csv(TIDY_ATTESTATION_CSV, index=False)

    grouped_df = project_summary(df)
    grouped_df.to_csv(PROJECT_SUMMARY_CSV, index=False)


if __name__ == "__main__":
    main()
