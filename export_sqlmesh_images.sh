#!/bin/bash

# Function to process file contents
process_file_contents() {
    local filename="$1"
    filename_no_ext="${filename%.*}"
    # Replace this echo with your desired function logic
    cat "$source_path/$filename" | carbon-now --save-as "$image_path/${filename_no_ext}"
}

# Directory to process
directory_path="$1"
source_path="${directory_path}/source"
image_path="${directory_path}/image"

# Check if directory path is provided
if [ -z "$directory_path" ]; then
    echo "Usage: $0 <directory_path>"
    exit 1
fi

# Check if the provided path is a directory
if [ ! -d "$directory_path" ]; then
    echo "Error: $directory_path is not a directory."
    exit 1
fi

# Iterate over all files in the directory
for file in "$source_path"/*; do
    if [ -f "$file" ]; then
        basename=$(basename "$file")
        process_file_contents "$basename"
    fi
done