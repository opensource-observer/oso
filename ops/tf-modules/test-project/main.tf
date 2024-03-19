terraform {
  required_providers {
    google-beta = {
      version = "~> 5.19.0"
    }
    google = {
      version = "~> 5.21.0"
    }
  }
}

resource "google_org_policy_policy" "short_iam_ttl" {
  provider = google
  name     = "projects/${google_project.project.name}/policies/iam.serviceAccountKeyExpiryHours"
  parent   = "projects/${google_project.project.name}"

  spec {
    #reset               = true
    inherit_from_parent = false
    rules {
      values {
        allowed_values = ["1h"]
      }
    }
  }
}

resource "google_project" "project" {
  project_id = var.project_name
  name       = var.project_name
  org_id     = var.organization_id
}

##
# Dummy service account
#
# This is used to create a service account that has no permissions at all. This
# is necessary for things like sqlfluff and dbt on the ci-default pipeline
##
resource "google_service_account" "dummy_sa" {
  project      = google_project.project.name
  account_id   = "oso-test-dummy"
  display_name = "Dummy account for test pipelines"
}

##
# BigQuery admin
#
# A bigquery admin user that can create datasets
##
resource "google_service_account" "bq_admin" {
  project      = google_project.project.name
  account_id   = "bigquery-admin"
  display_name = "BigQuery admin for the test account"
}

resource "google_project_iam_member" "bq_admin_binding" {
  project = google_project.project.id
  role    = "roles/bigquery.admin"

  member = "serviceAccount:${google_service_account.bq_admin.email}"
}

resource "google_project_iam_member" "admins" {
  project = google_project.project.id
  role    = "roles/owner"

  for_each = toset(var.admin_principals)

  member = "serviceAccount:${each.key}"
}
