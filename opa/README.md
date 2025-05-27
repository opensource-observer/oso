# Open Policy Agent (OPA) Configurations

This directory contains configurations and policies for the [Open Policy Agent](https://www.openpolicyagent.org/docs) (OPA).

OPA is used in this project to manage and enforce policies. For example, policies related to Trino access control can be found in the `trino/` subdirectory.

## Usage

First, you will need to install the [OPA CLI](https://www.openpolicyagent.org/docs#running-opa)

To use these OPA policies, you need to build them into a bundle and then upload this bundle to the OPA server or a designated storage location.

### Testing

Before building and uploading to production, run the policy tests with the following command:

```sh
opa test -v .
```

### Building the Policy Bundle

Navigate to the root directory of your policies in your terminal and run the following OPA command:

```sh
opa build .
```

This command compiles all the Rego files (`.rego`) and data files (`.json` or `.yaml`) in the current directory (and its subdirectories) into a gzipped tarball, typically named `bundle.tar.gz`. This bundle contains everything OPA needs to evaluate your policies.

### Uploading to GCS

Upload the generated policy bundle to the Google Cloud Storage bucket. OPA servers are configured to retrieve policies from this bucket.

```sh
gcloud storage cp bundle.tar.gz gs://oso-opa-policies/
```
