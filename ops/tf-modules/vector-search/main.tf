data "google_project" "project" {}

locals {
  deployed_index_display_name = "${var.name_prefix}-deployed-index"
  deployed_index_id           = replace("${var.name_prefix}-deployed-index", "-", "_")

  index_endpoint_display_name = "${var.name_prefix}-endpoint"
  index_display_name          = "${var.name_prefix}-index"

  ip_alloc_name = "${var.name_prefix}-vertex-ip-alloc"
}

resource "google_vertex_ai_index_endpoint_deployed_index" "deployed_index" {
  deployed_index_id     = local.deployed_index_id
  display_name          = local.deployed_index_display_name
  region                = var.region
  index                 = google_vertex_ai_index.index.id
  index_endpoint        = google_vertex_ai_index_endpoint.vertex_index_endpoint_deployed.id
  enable_access_logging = false
}

resource "google_vertex_ai_index" "index" {
  region              = var.region
  display_name        = local.index_display_name
  description         = var.index_description
  index_update_method = var.index_update_method
  labels              = var.labels

  metadata {
    contents_delta_uri = "gs://${google_storage_bucket.bucket.name}/contents"

    config {
      dimensions                  = var.dimensions
      approximate_neighbors_count = var.approximate_neighbors_count
      shard_size                  = var.shard_size
      distance_measure_type       = var.distance_measure_type

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 7
        }
      }
    }
  }
}

resource "google_vertex_ai_index_endpoint" "vertex_index_endpoint_deployed" {
  display_name = local.index_endpoint_display_name
  description  = "A vertex endpoint"
  region       = var.region
  network      = "projects/${data.google_project.project.number}/global/networks/${data.google_compute_network.vertex_network.name}"
  labels       = var.labels

  depends_on   = [
    google_service_networking_connection.vertex_vpc_connection
  ]
}

resource "google_storage_bucket" "bucket" {
  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true

  soft_delete_policy {
    retention_duration_seconds = 0
  }
}

resource "google_service_networking_connection" "vertex_vpc_connection" {
  network                 = data.google_compute_network.vertex_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = local.ip_alloc_name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = data.google_compute_network.vertex_network.id
}

data "google_compute_network" "vertex_network" {
  name = var.gcp_network
}
