#!/bin/bash
set -euxo pipefail

dagster asset materialize -m oso_dagster.definitions --select base_blocks
dagster asset materialize -m oso_dagster.definitions --select base_transactions
dagster asset materialize -m oso_dagster.definitions --select base_traces
dagster asset materialize -m oso_dagster.definitions --select frax_transactions
dagster asset materialize -m oso_dagster.definitions --select mode_transactions
dagster asset materialize -m oso_dagster.definitions --select pgn_transactions
dagster asset materialize -m oso_dagster.definitions --select frax_blocks
dagster asset materialize -m oso_dagster.definitions --select frax_traces
dagster asset materialize -m oso_dagster.definitions --select mode_blocks
dagster asset materialize -m oso_dagster.definitions --select mode_traces
dagster asset materialize -m oso_dagster.definitions --select pgn_blocks
dagster asset materialize -m oso_dagster.definitions --select pgn_traces
dagster asset materialize -m oso_dagster.definitions --select zora_blocks
dagster asset materialize -m oso_dagster.definitions --select zora_transactions
dagster asset materialize -m oso_dagster.definitions --select zora_traces
