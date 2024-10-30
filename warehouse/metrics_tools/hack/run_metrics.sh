#!/bin/bash
#

version=$1

mkdir -p /scratch/duckdb
mkdir -p /scratch/downloads

# Download everything to duckdb
python load_sources.py \
    --gcs-bucket-name oso-dataset-transfer-bucket \
    --gcs-bucket-path metrics-backstop \
    --db-path /scratch/duckdb/metrics.db \
    --download-path /scratch/downloads \
    --version $version

