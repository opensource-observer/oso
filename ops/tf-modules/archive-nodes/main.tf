data "google_project" "project" {}

locals {
  gcp_network = "${var.network_name}-vpc"

  arbitrum_one_disk_name      = "arbitrum-one-archive-node-disk"
  arbitrum_one_startup_script = "${var.scripts_path}/archive-node-startup.sh"
  ethereum_disk_name          = "ethereum-archive-node-disk"
  ethereum_startup_script     = "${var.scripts_path}/archive-node-startup.sh"
}

# Network setup

data "google_compute_network" "archive_node_network" {
  name = local.gcp_network
}

resource "google_compute_subnetwork" "archive_node_subnet" {
  name          = "archive-node-subnet"
  network       = data.google_compute_network.archive_node_network.id
  region        = var.region
  ip_cidr_range = "10.1.0.0/24"
  secondary_ip_range {
    range_name    = "archive-node-secondary-range"
    ip_cidr_range = "172.17.0.0/24"
  }
}

resource "google_compute_firewall" "tailscale_firewall_ipv4" {
  name    = "archive-node-tailscale-firewall-ipv4"
  network = data.google_compute_network.archive_node_network.id

  allow {
    protocol = "udp"
    ports    = ["41641"]
  }

  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "tailscale_firewall_ipv6" {
  name    = "archive-node-tailscale-firewall-ipv6"
  network = data.google_compute_network.archive_node_network.id

  allow {
    protocol = "udp"
    ports    = ["41641"]
  }

  source_ranges = ["::/0"]
}

resource "google_dns_policy" "tailnet_policy" {
  name                      = "tailnet-policy"
  enable_inbound_forwarding = true

  enable_logging = true

  networks {
    network_url = data.google_compute_network.archive_node_network.id
  }
}

# Arbitrum One Archive Node

resource "google_service_account" "arbitrum_one_sa" {
  account_id   = "arbitrum-one-archive-node-sa"
  display_name = "Custom SA for VM Instance"
}

resource "google_compute_disk" "arbitrum_one_ssd_disk" {
  name = "arbitrum-one-archive-node-ssd-disk"
  zone = var.zone
  type = "pd-ssd"
  size = 10000
}

resource "google_compute_instance" "arbitrum_one" {
  name         = "arbitrum-one-archive-node"
  machine_type = "n1-highmem-4"
  zone         = var.zone
  tags = [
    "arbitrum-one",
    "archive-node"
  ]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  # attached_disk {
  #   source      = google_compute_disk.arbitrum_one_ssd_disk.name
  #   mode        = "READ_WRITE"
  #   device_name = "arbitrum-mainnet-ssd"
  # }

  network_interface {
    network    = data.google_compute_network.archive_node_network.id
    subnetwork = google_compute_subnetwork.archive_node_subnet.id
    access_config {

    }
  }

  can_ip_forward = true

  metadata_startup_script = file(local.arbitrum_one_startup_script)

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = google_service_account.arbitrum_one_sa.email
    scopes = ["cloud-platform"]
  }
}

# Arbitrum One Archive Node (Large Scratch)
# NOTE: This instance uses local SSDs for scratch space, which are ephemeral.
# The data on them will be lost if the instance is stopped.
# It also attaches the same persistent disk as the other arbitrum_one instance.
# Only one of these instances can be running at a time to have read-write access to the disk.
resource "google_compute_instance" "arbitrum_one_large_scratch" {
  name         = "arbitrum-one-archive-node-large-scratch"
  machine_type = "n1-highmem-4"
  zone         = var.zone
  tags = [
    "arbitrum-one",
    "archive-node",
    "large-scratch"
  ]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  attached_disk {
    source      = google_compute_disk.arbitrum_one_ssd_disk.name
    mode        = "READ_WRITE"
    device_name = "arbitrum-mainnet"
  }

  // n1-highmem-4 supports up to 24 local SSDs of 375GB each, for a total of 9TB.
  // The user requested 10TB, so we are using the maximum available.
  dynamic "scratch_disk" {
    for_each = range(24)
    content {
      interface = "NVME"
    }
  }

  network_interface {
    network    = data.google_compute_network.archive_node_network.id
    subnetwork = google_compute_subnetwork.archive_node_subnet.id
    access_config {

    }
  }

  can_ip_forward = true

  metadata_startup_script = file(local.arbitrum_one_startup_script)

  service_account {
    # Google recommends custom service accounts that have cloud-platform scope and permissions granted via IAM Roles.
    email  = google_service_account.arbitrum_one_sa.email
    scopes = ["cloud-platform"]
  }
}

# Ethereum Mainnet Archive Node

resource "google_service_account" "ethereum_sa" {
  account_id   = "ethereum-archive-node-sa"
  display_name = "Custom SA for VM Instance"
}

resource "google_compute_disk" "ethereum_disk" {
  name = local.ethereum_disk_name
  zone = var.zone
  type = "pd-ssd"
  size = 16000
}

resource "google_compute_instance" "ethereum" {
  name         = "ethereum-archive-node"
  machine_type = "n1-highmem-4"
  zone         = var.zone
  tags = [
    "ethereum",
    "archive-node"
  ]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  attached_disk {
    source      = google_compute_disk.ethereum_disk.name
    mode        = "READ_WRITE"
    device_name = "ethereum-mainnet"
  }

  network_interface {
    network    = data.google_compute_network.archive_node_network.id
    subnetwork = google_compute_subnetwork.archive_node_subnet.id
    access_config {

    }
  }

  can_ip_forward = true

  metadata_startup_script = file(local.ethereum_startup_script)

  service_account {
    email  = google_service_account.ethereum_sa.email
    scopes = ["cloud-platform"]
  }
}
