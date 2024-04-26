locals {
  main_subnet_name           = "${var.cluster_name}-subnet"
  subnet_range_pods_name     = "${local.main_subnet_name}-pods"
  subnet_range_services_name = "${local.main_subnet_name}-services"
  node_service_account_id    = "${var.cluster_name}-node"
  node_service_account_email = "${local.node_service_account_id}@${var.project_id}.iam.gserviceaccount.com"
  node_pools = concat([
    {
      name               = "${var.cluster_name}-default-node-pool"
      machine_type       = "e2-medium"
      node_locations     = join(",", var.cluster_zones)
      min_count          = 0
      max_count          = 3
      local_ssd_count    = 0
      spot               = false
      disk_size_gb       = 75
      disk_type          = "pd-standard"
      image_type         = "COS_CONTAINERD"
      enable_gcfs        = false
      enable_gvnic       = false
      logging_variant    = "DEFAULT"
      auto_repair        = true
      auto_upgrade       = true
      service_account    = local.node_service_account_email
      preemptible        = false
      initial_node_count = 1
    },
    {
      name               = "${var.cluster_name}-spot-node-pool"
      machine_type       = "n1-standard-16"
      node_locations     = join(",", var.cluster_zones)
      min_count          = 0
      max_count          = 16
      local_ssd_count    = 0
      spot               = true
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "COS_CONTAINERD"
      enable_gcfs        = false
      enable_gvnic       = false
      logging_variant    = "DEFAULT"
      auto_repair        = true
      auto_upgrade       = true
      service_account    = local.node_service_account_email
      preemptible        = false
      initial_node_count = 0
    },
    {
      name               = "${var.cluster_name}-preemptible-node-pool"
      machine_type       = "n1-standard-64"
      node_locations     = join(",", var.cluster_zones)
      min_count          = 0
      max_count          = 16
      local_ssd_count    = 0
      spot               = false
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      image_type         = "COS_CONTAINERD"
      enable_gcfs        = false
      enable_gvnic       = false
      logging_variant    = "DEFAULT"
      auto_repair        = true
      auto_upgrade       = true
      service_account    = local.node_service_account_email
      preemptible        = true
      initial_node_count = 0
    },
  ], var.extra_node_pools)

  node_pool_labels = merge({
    "${var.cluster_name}-default-node-pool" = {
      default_node_pool = true
      pool_type         = "persistent"
    }
    "${var.cluster_name}-spot-node-pool" = {
      default_node_pool = false
      pool_type         = "spot"
    }
    "${var.cluster_name}-preemptible-node-pool" = {
      default_node_pool = false
      pool_type         = "preemptible"
    }
  }, var.extra_node_labels)

  node_pool_metadata = merge({
    "${var.cluster_name}-default-node-pool" = {
      node-pool-metadata-custom-value = "my-node-pool"
    }
  }, var.extra_node_metadata)

  node_pool_taints = merge({
    "${var.cluster_name}-spot-node-pool" = [
      {
        key    = "pool_type"
        value  = "spot"
        effect = "PREFER_NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-preemptible-node-pool" = [
      {
        key    = "pool_type"
        value  = "preemptible"
        effect = "PREFER_NO_SCHEDULE"
      },
    ]
  }, var.extra_node_taints)

  node_pool_tags = merge({
    "${var.cluster_name}-default-node-pool" = [
      "default-node-pool",
    ]
    "${var.cluster_name}-spot-node-pool" = [
      "spot",
    ]
    "${var.cluster_name}-preemptible-node-pool" = [
      "preemptible",
    ]
  }, var.extra_node_tags)

  node_pool_oauth_scopes = merge({
    all = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
    ]
  }, var.extra_pool_oauth_scopes)
}

resource "google_service_account" "node_service_account" {
  account_id   = "${var.cluster_name}-node"
  display_name = "Service account for the node pools"
}

module "vpc" {
  source  = "terraform-google-modules/network/google"
  version = "~> 9.1"

  project_id   = var.project_id
  network_name = "${var.cluster_name}-vpc"
  routing_mode = "GLOBAL"

  subnets = [
    {
      subnet_name   = local.main_subnet_name
      subnet_ip     = var.main_subnet_cidr
      subnet_region = var.cluster_region
    },
  ]

  secondary_ranges = {
    "${local.main_subnet_name}" = [
      {
        range_name    = local.subnet_range_pods_name
        ip_cidr_range = var.pods_cidr
      },
      {
        range_name    = local.subnet_range_services_name
        ip_cidr_range = var.services_cidr
      }
    ]
  }

  routes = [
    {
      name              = "${var.cluster_name}-egress-internet"
      description       = "route through IGW to access internet"
      destination_range = "0.0.0.0/0"
      tags              = "egress-inet"
      next_hop_internet = "true"
    },
  ]
}


module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  project_id                 = var.project_id
  name                       = var.cluster_name
  region                     = var.cluster_region
  zones                      = var.cluster_zones
  network                    = module.vpc.network_name
  subnetwork                 = local.main_subnet_name
  ip_range_pods              = local.subnet_range_pods_name
  ip_range_services          = local.subnet_range_services_name
  http_load_balancing        = var.enable_http_load_balancing
  network_policy             = false
  horizontal_pod_autoscaling = true
  filestore_csi_driver       = false
  deletion_protection        = false

  node_pools = local.node_pools

  node_pools_oauth_scopes = local.node_pool_oauth_scopes

  node_pools_labels = local.node_pool_labels

  node_pools_metadata = local.node_pool_metadata

  node_pools_taints = local.node_pool_taints

  node_pools_tags = local.node_pool_tags
}
