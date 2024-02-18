#!/bin/bash
# Creates a dbt profile for the OSO data warehouse
# 
# Usage: create-dbt-profile.sh [dataset] [service-account-path]
# 
# The dataset should be either opensource_observer or
# opensource_observer_staging

set -euo pipefail

mkdir -p ~/.dbt

dataset=$1
service_account_path=$2

cat <<EOF > ~/.dbt/profiles.yml
opensource_observer:
  target: release
  outputs:
    release:
      type: bigquery
      dataset: ${dataset} 
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: service-account
      keyfile: ${service_account_path}
      project: oso-production
      threads: 1
EOF