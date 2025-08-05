locals {
  main_subnet_name           = "${var.cluster_name}-subnet"
  subnet_range_pods_name     = "${local.main_subnet_name}-pods"
  subnet_range_services_name = "${local.main_subnet_name}-services"
  node_service_account_id    = "${var.cluster_name}-node"
  node_service_account_email = "${local.node_service_account_id}@${var.project_id}.iam.gserviceaccount.com"
  node_pools = concat([
    {
      name               = "${var.cluster_name}-default-node-pool"
      machine_type       = "e2-standard-4"
      node_locations     = join(",", var.default_node_pool_cluster_zones)
      min_count          = 0
      max_count          = 4
      local_ssd_count    = 0
      spot               = false
      disk_size_gb       = 50
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
    # A non-spot non-preemptible set of nodes for job execution. Nothing should run here except temporary jobs
    {
      name               = "${var.cluster_name}-standard-node-pool"
      machine_type       = "e2-standard-4"
      node_locations     = join(",", var.cluster_zones)
      min_count          = 0
      max_count          = 8
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
      preemptible        = false
      initial_node_count = 0
    },
    # The spot pool is for workloads that need spot
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
    # The preemptible pool should be used only if spot can't be used
    {
      name               = "${var.cluster_name}-preemptible-node-pool"
      machine_type       = "n1-standard-16"
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
    # Trino coordinator pool
    {
      name                              = "${var.cluster_name}-trino-coordinator-node-pool"
      machine_type                      = "n1-highmem-8"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 1
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 0
      spot                              = false
      disk_size_gb                      = 150
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },
    # Trino worker pool
    {
      name                              = "${var.cluster_name}-trino-worker-node-pool"
      machine_type                      = "m1-ultramem-80"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 20
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 0
      spot                              = true
      disk_size_gb                      = 200
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },
    # Trino consumer coordinator pool
    {
      name                              = "${var.cluster_name}-cons-trino-coord-node-pool"
      machine_type                      = "n1-highmem-2"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 1
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 0
      spot                              = false
      disk_size_gb                      = 75
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },
    # Trino consumer worker pool
    {
      name                              = "${var.cluster_name}-cons-trino-worker-node-pool"
      machine_type                      = "n1-highmem-8"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 5
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 0
      spot                              = true
      disk_size_gb                      = 100
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },
    # MCS (Metrics Calculation Service) scheduler
    {
      name                              = "${var.cluster_name}-mcs-scheduler-node-pool"
      machine_type                      = "n1-highmem-4"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 4
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 0
      spot                              = false
      disk_size_gb                      = 100
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },

    # MCS Workers
    {
      name                              = "${var.cluster_name}-mcs-worker-node-pool"
      machine_type                      = "n1-highmem-64"
      node_locations                    = join(",", var.cluster_zones)
      min_count                         = 0
      max_count                         = 25
      local_ssd_count                   = 0
      local_ssd_ephemeral_storage_count = 3
      spot                              = true
      disk_size_gb                      = 100
      disk_type                         = "pd-standard"
      image_type                        = "COS_CONTAINERD"
      enable_gcfs                       = false
      enable_gvnic                      = false
      logging_variant                   = "DEFAULT"
      auto_repair                       = true
      auto_upgrade                      = true
      service_account                   = local.node_service_account_email
      preemptible                       = false
      initial_node_count                = 0
    },

  ], var.extra_node_pools)

  node_pool_labels = merge({
    "${var.cluster_name}-default-node-pool" = {
      default_node_pool = true
      pool_type         = "persistent"
    }
    "${var.cluster_name}-standard-node-pool" = {
      default_node_pool = false
      pool_type         = "standard"
    }
    "${var.cluster_name}-spot-node-pool" = {
      default_node_pool = false
      pool_type         = "spot"
    }
    "${var.cluster_name}-preemptible-node-pool" = {
      default_node_pool = false
      pool_type         = "preemptible"
    }
    "${var.cluster_name}-trino-worker-node-pool" = {
      default_node_pool = false
      pool_type         = "trino-worker"
    }
    "${var.cluster_name}-trino-coordinator-node-pool" = {
      default_node_pool = false
      pool_type         = "trino-coordinator"
    }
    "${var.cluster_name}-cons-trino-worker-node-pool" = {
      default_node_pool = false
      pool_type         = "cons-trino-worker"
    }
    "${var.cluster_name}-cons-trino-coord-node-pool" = {
      default_node_pool = false
      pool_type         = "cons-trino-coord"
    }
    "${var.cluster_name}-mcs-scheduler-node-pool" = {
      default_node_pool = false
      pool_type         = "mcs-scheduler"
    }
    "${var.cluster_name}-mcs-worker-node-pool" = {
      default_node_pool = false
      pool_type         = "mcs-worker"
    }
  }, var.extra_node_labels)

  node_pool_metadata = merge({
    "${var.cluster_name}-default-node-pool" = {
      node-pool-metadata-custom-value = "my-node-pool"
    }
  }, var.extra_node_metadata)

  node_pool_taints = merge({
    "${var.cluster_name}-standard-node-pool" = [
      {
        key    = "pool_type"
        value  = "standard"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-spot-node-pool" = [
      {
        key    = "pool_type"
        value  = "spot"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-preemptible-node-pool" = [
      {
        key    = "pool_type"
        value  = "preemptible"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-trino-worker-node-pool" = [
      {
        key    = "pool_type"
        value  = "trino-worker"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-trino-coordinator-node-pool" = [
      {
        key    = "pool_type"
        value  = "trino-coordinator"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-cons-trino-worker-node-pool" = [
      {
        key    = "pool_type"
        value  = "cons-trino-worker"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-cons-trino-coord-node-pool" = [
      {
        key    = "pool_type"
        value  = "cons-trino-coord"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-mcs-scheduler-node-pool" = [
      {
        key    = "pool_type"
        value  = "mcs-scheduler"
        effect = "NO_SCHEDULE"
      },
    ]
    "${var.cluster_name}-mcs-worker-node-pool" = [
      {
        key    = "pool_type"
        value  = "mcs-worker"
        effect = "NO_SCHEDULE"
      },
    ]
  }, var.extra_node_taints)

  node_pool_tags = merge({
    "${var.cluster_name}-default-node-pool" = [
      "default-node-pool",
    ]
    "${var.cluster_name}-standard-node-pool" = [
      "standard",
    ]
    "${var.cluster_name}-spot-node-pool" = [
      "spot",
    ]
    "${var.cluster_name}-preemptible-node-pool" = [
      "preemptible",
    ]
    "${var.cluster_name}-trino-worker-pool" = [
      "trino-worker",
    ]
    "${var.cluster_name}-trino-coordinator-pool" = [
      "trino-coordinator",
    ]
    "${var.cluster_name}-cons-trino-worker-pool" = [
      "cons-trino-worker",
    ]
    "${var.cluster_name}-cons-trino-coord-pool" = [
      "cons-trino-coord",
    ]
    "${var.cluster_name}-mcs-scheduler-pool" = [
      "mcs-scheduler",
    ]
    "${var.cluster_name}-mcs-worker-pool" = [
      "mcs-worker",
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
      subnet_name           = local.main_subnet_name
      subnet_ip             = var.main_subnet_cidr
      subnet_region         = var.cluster_region
      subnet_private_access = true
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
  source                               = "terraform-google-modules/kubernetes-engine/google"
  version                              = "~> 35.0.0"
  project_id                           = var.project_id
  name                                 = var.cluster_name
  region                               = var.cluster_region
  zones                                = var.cluster_zones
  network                              = module.vpc.network_name
  subnetwork                           = local.main_subnet_name
  ip_range_pods                        = local.subnet_range_pods_name
  ip_range_services                    = local.subnet_range_services_name
  http_load_balancing                  = var.enable_http_load_balancing
  network_policy                       = false
  horizontal_pod_autoscaling           = true
  filestore_csi_driver                 = false
  gcs_fuse_csi_driver                  = true
  deletion_protection                  = false
  monitoring_enable_managed_prometheus = true
  logging_enabled_components           = ["SYSTEM_COMPONENTS", "APISERVER", "SCHEDULER", "CONTROLLER_MANAGER", "WORKLOADS"]
  monitoring_enabled_components        = ["SYSTEM_COMPONENTS", "APISERVER", "SCHEDULER", "CONTROLLER_MANAGER"]

  node_pools = local.node_pools

  node_pools_oauth_scopes = local.node_pool_oauth_scopes

  node_pools_labels = local.node_pool_labels

  node_pools_metadata = local.node_pool_metadata

  node_pools_taints = local.node_pool_taints

  node_pools_tags = local.node_pool_tags
}

# Dagster bucket. In the future it would make more sense that this is managed at
# the application level (e.g. some k1bernetes operator)
resource "google_storage_bucket" "dagster" {
  name          = "${var.dagster_bucket_prefix}-dagster-bucket"
  location      = var.dagster_bucket_location
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "dagster_bucket_admin" {
  for_each = toset(var.dagster_bucket_rw_principals)
  bucket   = google_storage_bucket.dagster.name
  role     = "roles/storage.admin"
  member   = each.key
}
