#!/bin/bash

set -uxo pipefail

# Variables
file_path=$1
endpoint_url=$2

export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required

# Delete the file from S3
aws s3 rm "$file_path" --endpoint-url="$endpoint_url"

# Check if the delete was successful
if [ $? -eq 0 ]; then
  echo "File $file_path deleted"
else
  echo "Failed to delete file $file_path"
  exit 1
fi
