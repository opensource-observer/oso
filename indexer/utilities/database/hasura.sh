#!bin/bash

SCRIPT_RELATIVE_DIR=$(dirname "${BASH_SOURCE[0]}") 
ENV_FILE=$SCRIPT_RELATIVE_DIR/../../.env

source $ENV_FILE
docker run --rm -it \
  -p 8080:8080 \
  --env-file $ENV_FILE \
  --env HASURA_GRAPHQL_ENABLE_CONSOLE=true \
  --env HASURA_GRAPHQL_DATABASE_URL=postgres://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_DATABASE \
  hasura/graphql-engine
  #psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_DATABASE
