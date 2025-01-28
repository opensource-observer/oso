#!/bin/bash

set -uxo pipefail

# Variables
file_path=$1
object_name=$2
endpoint_url=$3

# Upload the file to S3
aws s3 cp "$file_path" "s3://$BUCKET_NAME/$object_name" --endpoint-url="$endpoint_url" --debug

# Check if the upload was successful
if [ $? -eq 0 ]; then
  echo "File $file_path uploaded to $BUCKET_NAME/$object_name"
else
  echo "Failed to upload file $file_path"
  exit 1
fi