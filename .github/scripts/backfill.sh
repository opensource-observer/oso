#!/bin/bash
# Usage backfill $collector $start_date $backfill_interval_days [$end_date]
set -euo pipefail

collector=$1
start_date=$2
backfill_interval_days=$3
end_date="${4:-}"

args=( "--start-date=${start_date}" "--backfill-interval-days=${backfill_interval_days}")
if [[ ! -z $end_date ]]; then
    args+=("--end-date=${end_date}")
fi

pnpm start:indexer scheduler job backfill "${collector}" "${args[@]}"