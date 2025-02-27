# Terraform module for setting up the data warehouse. These modules
# are provided so that one could easily replicate the infrastructure required to
# run the data warehouse. 

# Once the OpenTofu registry is GA, we will publish this terraform code to the
# OpenTofu registry.

# What does this module provide?
# 
# - A publicly accessible BigQuery Dataset
# - CloudSQL instance(s)
# - A bucket to allow for transfers from bigquery to cloudsql
# - A service accounts that can be used by DBT and bq2cloudsql

data "google_project" "project" {}

locals {
  admin_service_account_name    = "${var.name}-admin"
  readonly_service_account_name = "${var.name}-readonly"
  dataset_id                    = replace(var.name, "-", "_")
  raw_dataset_id                = replace("${var.name}_raw_sources", "-", "_")
}

###
# Google service account to administer the data warehouse
###
resource "google_service_account" "warehouse_admin" {
  account_id   = local.admin_service_account_name
  display_name = "Admin service account for ${var.name}"
}

###
# Read only service account - for outside applications to use
###
resource "google_service_account" "warehouse_readonly" {
  account_id   = local.readonly_service_account_name
  display_name = "Read only service account for ${var.name}"
}

###
# Additional bucket_rw users that are managed by this terraform module
###
resource "google_service_account" "managed_bucket_rw_user" {
  for_each = toset(var.additional_bucket_rw_service_account_names)

  account_id   = each.key
  display_name = "A bucket rw service account ${each.key}"
}


###
# BigQuery Dataset
###
resource "google_bigquery_dataset" "dataset" {
  dataset_id    = local.dataset_id
  friendly_name = var.dataset_name
  description   = var.dataset_description
  location      = var.dataset_location

  labels = {
    environment = var.environment
    dw_name     = var.name
  }

  access {
    role          = "OWNER"
    user_by_email = google_service_account.warehouse_admin.email
  }

  ###
  # Allow public access
  ###
  access {
    role          = "READER"
    special_group = "allAuthenticatedUsers"
  }
}

###
# A dataset for receiving data
###
resource "google_bigquery_dataset" "raw_dataset" {
  dataset_id    = local.raw_dataset_id
  friendly_name = "Raw data sources for: ${local.dataset_id}"
  description   = "Raw data sources for: ${local.dataset_id}"
  location      = var.dataset_location

  labels = {
    environment = var.environment
    dw_name     = var.name
  }

  access {
    role          = "OWNER"
    user_by_email = google_service_account.warehouse_admin.email
  }

  ###
  # Allow public access
  ###
  access {
    role          = "READER"
    special_group = "allAuthenticatedUsers"
  }
}

###
# GCS Bucket
###
resource "google_storage_bucket" "dataset_transfer" {
  name          = "${var.name}-dataset-transfer-bucket"
  location      = var.dataset_location
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "random_password" "metadata_user_temp_password" {
  length  = 24
  special = true
}

###
# CloudSQL instance
###
module "warehouse_cloudsql" {
  source  = "GoogleCloudPlatform/sql-db/google//modules/postgresql"
  version = "8.0.0"

  count = length(var.cloudsql_databases)

  project_id       = data.google_project.project.project_id
  database_version = var.cloudsql_databases[count.index].database_version
  tier             = var.cloudsql_databases[count.index].tier
  user_name        = var.cloudsql_databases[count.index].user_name
  zone             = var.cloudsql_databases[count.index].zone
  name             = var.cloudsql_databases[count.index].name
  user_labels = {
    dw_name = var.name
  }
  ip_configuration    = var.cloudsql_databases[count.index].ip_configuration
  deletion_protection = var.cloudsql_databases[count.index].deletion_protection

  additional_databases = var.cloudsql_databases[count.index].additional_databases

  # At the moment this user needs to be manual configured with permissions to
  # the metadata database
  additional_users = var.cloudsql_databases[count.index].additional_users
}

resource "google_project_iam_member" "project" {
  count    = length(var.cloudsql_databases)
  for_each = toset(var.additional_cloudsql_client_principals)
  project  = data.google_project.project.project_id
  role     = "roles/cloudsql.client"
  member   = each.value

  condition {
    title       = "only_${local.dataset_id}_db_client"
    description = "Restrict access to a database instance: ${var.cloudsql_databases[count.index].name}"
    expression  = "resource.name.startsWith(\"projects/${data.google_project.project.project_id}/instances/${var.cloudsql_databases[count.index].name}\")"
  }
}

###
# Add permissions for the cloudsql user to read from the bucket
###
resource "google_storage_bucket_iam_member" "cloudsql_member" {
  bucket = google_storage_bucket.dataset_transfer.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${module.warehouse_cloudsql.instance_service_account_email_address}"
}

###
# Add permissions for users to read/write 
##
resource "google_storage_bucket_iam_member" "bucket_rw_read" {
  for_each = toset(var.bucket_rw_principals)
  bucket   = google_storage_bucket.dataset_transfer.name
  role     = "roles/storage.objectViewer"
  member   = each.key
}

resource "google_storage_bucket_iam_member" "bucket_rw_write" {
  for_each = toset(var.bucket_rw_principals)
  bucket   = google_storage_bucket.dataset_transfer.name
  role     = "roles/storage.objectCreator"
  member   = each.key
}

resource "google_storage_bucket_iam_member" "managed_bucket_rw_read" {
  for_each = toset(var.additional_bucket_rw_service_account_names)
  bucket   = google_storage_bucket.dataset_transfer.name
  role     = "roles/storage.objectViewer"
  member   = "serviceAccount:${google_service_account.managed_bucket_rw_user[each.key].email}"
}

resource "google_storage_bucket_iam_member" "managed_bucket_rw_write" {
  for_each = toset(var.additional_bucket_rw_service_account_names)
  bucket   = google_storage_bucket.dataset_transfer.name
  role     = "roles/storage.objectCreator"
  member   = "serviceAccount:${google_service_account.managed_bucket_rw_user[each.key].email}"
}

###
# Service account permissions
###
resource "google_project_iam_custom_role" "readonly_custom_role" {
  role_id     = "${local.dataset_id}_readonly"
  title       = "Read-Only Role for ${local.dataset_id}"
  description = "Read-Only Role for ${local.dataset_id}"
  permissions = [
    "bigquery.datasets.get",
    "bigquery.datasets.getIamPolicy",
    "bigquery.jobs.create",
    "bigquery.models.export",
    "bigquery.models.getData",
    "bigquery.models.getMetadata",
    "bigquery.models.list",
    "bigquery.routines.get",
    "bigquery.routines.list",
    "bigquery.tables.createSnapshot",
    "bigquery.tables.export",
    "bigquery.tables.get",
    "bigquery.tables.getData",
    "bigquery.tables.getIamPolicy",
    "bigquery.tables.list",
    "resourcemanager.projects.get",
  ]
}


resource "google_project_iam_member" "service_account_binding" {
  count   = length(var.cloudsql_databases)
  project = data.google_project.project.project_id
  role    = "roles/cloudsql.admin"

  member = "serviceAccount:${google_service_account.warehouse_admin.email}"

  condition {
    expression  = "resource.name == 'projects/${data.google_project.project.project_id}/instances/${var.cloudsql_databases[count.index].name}' && resource.type == 'sqladmin.googleapis.com/Instance'"
    title       = "created"
    description = "Cloud SQL instance creation"
  }
}

resource "google_storage_bucket_iam_member" "member" {
  bucket = google_storage_bucket.dataset_transfer.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.warehouse_admin.email}"
}

resource "google_project_iam_member" "bq_admin" {
  project = data.google_project.project.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.warehouse_admin.email}"
}

resource "google_project_iam_member" "readonly_custom_role" {
  project = data.google_project.project.project_id
  role    = google_project_iam_custom_role.readonly_custom_role.id
  member  = "serviceAccount:${google_service_account.warehouse_readonly.email}"
}
