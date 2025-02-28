#!/bin/bash

set -uxo pipefail

# Variables
source_path=$1
target_path=$2
endpoint_url=$3

export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required

# Upload the file to S3
aws s3 cp "$source_path" "$target_path" --endpoint-url="$endpoint_url"

# Check if the upload was successful
if [ $? -eq 0 ]; then
  echo "File $source_path copied to $target_path"
else
  echo "Failed to copy file $source_path"
  exit 1
fi
