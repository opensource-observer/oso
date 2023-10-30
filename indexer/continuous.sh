#!/bin/bash

# This is a hacky script to run backfill for stuff. You'll need to replace a couple variables

set -uxo pipefail

# Replace these next 4 variables to use this script. If things happen to break
# and you need to restart the process you will need to change the start/end
# date. You should see references to where it left off in the logs. You can just
# see the most updated log that's in `${log_dir}`
start_date="2018-01-25T00:00:00Z"  # Initial start date
end_date="2018-02-24T00:00:00Z"    # Initial end date
collector_name="github-issues"
base_dir="/tmp/oso"

log_dir="${base_dir}/logs"
cache_dir="${base_dir}/cache"
run_dir="${base_dir}/run"

mkdir -p "${base_dir}"
mkdir -p "${log_dir}"
mkdir -p "${cache_dir}"
mkdir -p "${run_dir}"

while true; do
  # Call your CLI command with the start and end dates
  pnpm start scheduler manual "${collector_name}" \
     --cache-dir "${cache_dir} \
     --run-dir "${run_dir}" \
     --start-date "${start_date}" \
     --end-date "${end_date}" \
     --execution-mode=all-at-once 2>&1 | tee "${log_dir}/${collector_name}-${start_date}.log

  # Increment the start and end dates for the next week
  start_date=$(date -u -d "$start_date + 30 days" "+%Y-%m-%dT%H:%M:%SZ")
  end_date=$(date -u -d "$end_date + 30 days" "+%Y-%m-%dT%H:%M:%SZ")

  # Break the loop if you reach a specific end date (optional)
  if [ "$start_date" \> "2023-10-24T00:00:00Z" ]; then
    break
  fi

  # Add a delay to control the rate of calls (e.g., 1 second)
  sleep 1
done
