#!/bin/bash

# Directory containing the seed files
SEED_DIR="/seed"

# Loop through each file in the seed directory
for file in "$SEED_DIR"/*; do
    if [ -f "$file" ]; then
        # Execute the trino command with the current file
        trino --server trino:8080 --file "$file"
    fi
done