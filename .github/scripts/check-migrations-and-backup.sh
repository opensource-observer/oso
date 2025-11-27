#!/bin/bash
set -euxo pipefail

# Arguments
WORKDIR=$1
SUPABASE_DB_URL=$2

if [ -z "$WORKDIR" ]; then
  echo "Error: WORKDIR is required."
  exit 1
fi

pushd "$WORKDIR"

if [ -z "$SUPABASE_DB_URL" ]; then
  echo "Error: SUPABASE_DB_URL is required."
  exit 1
fi

set +u
if [ -z "$GITHUB_OUTPUT" ]; then
  echo "GITHUB_OUTPUT is not set. Using /dev/null for local testing."
  GITHUB_OUTPUT="/dev/null"
fi
set -u

# Allow dry run mode for testing
DRY_RUN=${DRY_RUN:-false}

echo "Checking for pending migrations..."

# Capture output from dry-run
# pnpm supabase needs to be run where supabase config/migrations are (apps/frontend)
# usage of 2>&1 to capture stderr as well
OUTPUT=$(pnpm supabase db push --dry-run --db-url "$SUPABASE_DB_URL" 2>&1) || true
echo "$OUTPUT"

if echo "$OUTPUT" | grep -q "Remote database is up to date"; then
  echo "No migrations needed."
  echo "needs_migration=false" >> $GITHUB_OUTPUT
elif echo "$OUTPUT" | grep -q "Would push these migrations"; then
  echo "Migrations needed. Proceeding with backup."
  echo "needs_migration=true" >> $GITHUB_OUTPUT
  
  # Perform backup 
  TIMESTAMP=$(date -u +"%Y%m%d%H%M%S")
  BACKUP_FILE="${TIMESTAMP}Z_backup.sql.gz"
  
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "Dry run enabled, skipping actual backup creation."
    echo "backup_file=$BACKUP_FILE" >> $GITHUB_OUTPUT
  else
    echo "Running pg_dump..."
    pg_dump "$SUPABASE_DB_URL" | gzip > "$BACKUP_FILE"
    echo "Creating backup file: $BACKUP_FILE"
  fi
  
  echo "Backup created at $BACKUP_FILE"
  echo "backup_file=$BACKUP_FILE" >> $GITHUB_OUTPUT
else
  echo "Error: Unexpected output from dry run."
  echo "$OUTPUT"
  exit 1
fi

popd