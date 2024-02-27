#!/bin/bash
# Creates a dbt profile for the OSO data warehouse
# 
# Usage: create-dbt-profile.sh [dataset] [service-account-path]
# 
# The dataset should be either opensource_observer or
# opensource_observer_staging

set -euo pipefail

mkdir -p ~/.dbt

service_account_path=$1

cat <<EOF > ~/.dbt/profiles.yml
opensource_observer:
  target: production
  outputs:
    production:
      type: bigquery
      dataset: oso
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: service-account
      keyfile: ${service_account_path}
      project: ${GOOGLE_PROJECT_ID}
      threads: 1
    playground:
      type: bigquery
      dataset: oso_playground
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: service-account
      keyfile: ${service_account_path}
      project: ${GOOGLE_PROJECT_ID}
      threads: 1
EOF