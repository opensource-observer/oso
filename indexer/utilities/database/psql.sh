#!bin/bash

SCRIPT_RELATIVE_DIR=$(dirname "${BASH_SOURCE[0]}") 
ENV_FILE=$SCRIPT_RELATIVE_DIR/../../.env

source $ENV_FILE
docker run --rm -it \
  -v /tmp:/tmp \
  --env-file $ENV_FILE \
  postgres:15 \
  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_DATABASE