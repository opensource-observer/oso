#! /bin/bash

GREEN="\033[0;32m"
YELLOW="\033[1;33m"
ENDCOLOR="\033[0m"

function show_env_hint() {
  echo -e "[${YELLOW}Required ENV${ENDCOLOR}] $1 is not set."
  cat << EOF

Please set the following environment variables in your GitHub Codespaces Secrets.
You can set the secret in your GitHub Codespaces Secrets by going to:
    GitHub Personal Account -> Settings -> Codespaces -> Codespaces secrets

Then add the secret with the name $1 and the value of the secret.
After adding the secret, please restart the Codespaces to apply the changes.
EOF
}

# Check the ENV variables should be provided by the user
if [ -z "$DBT_GOOGLE_PROJECT" ]; then
  show_env_hint "DBT_GOOGLE_PROJECT"
  exit 1
fi

if [ -z "$DBT_GOOGLE_DATASET" ]; then
  show_env_hint "DBT_GOOGLE_DATASET"
  exit 1
fi

if [ -z "$DBT_GOOGLE_DEV_DATASET" ]; then
  show_env_hint "DBT_GOOGLE_DEV_DATASET"
  exit 1
fi

mkdir -p $HOME/.config/gcloud
DBT_GOOGLE_KEYFILE=$HOME/.config/gcloud/google-service-account.json

# Setup dbt profiles.yml
if [ "$DBT_PROFILES_YML_CONTENT" != '' ]; then
  echo "$DBT_PROFILES_YML_CONTENT" > $HOME/.dbt/profiles.yml
  echo "dbt profiles.yml is saved to $HOME/.dbt/profiles.yml"
fi


# Check if the user is already logged in
if [ -z "$GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY_CONTENT" ]; then
  # Change to use OAuth2 to login
  if [ -f "${DBT_GOOGLE_KEYFILE}" ]; then
    echo "User is already logged in Google cloud"
    gcloud auth list
    exit 0
  else
    echo -e "[${GREEN}Action${ENDCOLOR}] Please login to Google cloud to continue."
    gcloud auth application-default login
  fi
else
  # Use the service account key to login
  echo "$GOOGLE_CLOUD_SERVICE_ACCOUNT_KEY_CONTENT" > ${DBT_GOOGLE_KEYFILE}
  echo "Google cloud service account key is saved to ${DBT_GOOGLE_KEYFILE}"
fi
