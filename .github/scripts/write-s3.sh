#!/bin/bash

set -uxo pipefail

# Variables
FILE_PATH=$1
OBJECT_NAME=$2

# Upload the file to S3
aws s3 cp "$FILE_PATH" "s3://$BUCKET_NAME/$OBJECT_NAME" --endpoint-url="$AWS_ENDPOINT_URL"

# Check if the upload was successful
if [ $? -eq 0 ]; then
  echo "File $FILE_PATH uploaded to $BUCKET_NAME/$OBJECT_NAME"
else
  echo "Failed to upload file $FILE_PATH"
  exit 1
fi