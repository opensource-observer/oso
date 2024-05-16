#! /bin/bash

if [ "${CODESPACES}" == "true" ]; then
  # Set the default git repository if running in GitHub Codespaces
  echo "Setting the default git repository to $GITHUB_REPOSITORY"
  gh repo set-default $GITHUB_REPOSITORY

  current_branch=$(git branch --show-current)
  # Check if the current branch is under a pull request
  if gh pr view > /dev/null ; then
    # Check if the Recce state file is downloaded
    run_id=$(gh run list -b ${current_branch} -s success --limit 1 -w "${RECCE_CI_WORKFLOW_NAME}" --json databaseId | jq .[].databaseId)
    if [ -z "$run_id" ]; then
      echo "No successful Recce run found for the current branch."
    else
      echo "Downloading the Recce state file for the last successful run."
      gh run download $run_id --dir .recce
      echo "The Recce state file is downloaded to '.recce/recce_state_file/recce_state.json'."
    fi
  fi

  # Check daily staging artifact files
  default_branch=$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)
  daily_artifact_workflow_id=$(gh run list -w "${RECCE_DAILY_CI_WORKFLOW_NAME}" --status success -b dev --limit 1 --json databaseId | jq .[].databaseId)
  gh run download $daily_artifact_workflow_id --dir .recce
  if [ -d ".recce/dbt-artifacts" ]; then
    mv .recce/dbt-artifacts target-base
    echo "The daily staging artifact files are downloaded to 'target-base'."
  fi
fi