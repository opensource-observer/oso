#!/bin/bash

set -euo pipefail
# This would have been a javascript script but it's non-trivial there compared to
# bash.

iam_account=$1
output_file=$2

temp_dir=`mktemp -d`


list_keys() {
    iam_account=$1
    gcloud iam service-accounts keys list --format=json --iam-account="${iam_account}"
}

create_key() {
    iam_account=$1
    output_path=$2
    gcloud iam service-accounts keys create --iam-account="${iam_account}" "${output_path}"
}

delete_key() {
    iam_account=$1
    key_id=$2
    gcloud iam service-accounts keys delete -q --iam-account="${iam_account}" "${key_id}"
}

parse_user_managed() {
    jq -r '.[] | select(.keyType=="USER_MANAGED" and .validBeforeTime<="'"$(date +'%Y-%m-%dT%H:%M:%S')"'").name | split("/")[5]'
}

# Check for old keys
old_keys=$(list_keys "${iam_account}" | parse_user_managed)

# Delete any old keys
if [[ ! -z "$old_keys" ]]; then
    echo "${old_keys}" |  while read line ; do
        echo "Deleting $line"
        delete_key "${iam_account}" "${line}"
    done
fi

# Create a new key
create_key "${iam_account}" "${output_file}"