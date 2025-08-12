---
title: Archive Node Guide
sidebar_position: 7
---

This guide explains how to create and deploy blockchain archive nodes in the OSO infrastructure. Archive nodes maintain a complete history of blockchain transactions and state, enabling historical data analysis and queries.

## Overview

Archive nodes are essential infrastructure components that store the complete blockchain history, including:

- All historical transactions
- Smart contract interactions
- State changes over time
- Event logs and receipts

Our archive nodes run on Google Cloud Platform using Docker containers, with Tailscale for secure networking.

## Prerequisites

Before creating a new archive node, ensure you have:

### Required Access

- **Tailscale network access**: Authentication to OSO instances
- **Google Cloud access**: Permissions to create VMs, disks, and networking resources
- **Repository access**: Clone access to the `private-ops` repository
- **Terraform**: Installed locally for infrastructure management

### Authentication Setup

Authenticate with Google Cloud using both methods:

```bash
gcloud auth login
gcloud auth application-default login
```

### Required Tools

- [Terraform](https://www.terraform.io/downloads) (latest version)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install)
- SSH client
- Access to Tailscale admin panel

## Creating a New Archive Node

### Step 1: Configure Infrastructure

All VM configurations are stored in `oso/ops/tf-modules/archive-nodes/main.tf`. This file contains:

- Network configuration (VPC, subnets, firewall rules)
- VM instances with appropriate sizing
- Disk attachments for blockchain data storage
- Service accounts and IAM permissions

#### Example Configuration

The current implementation includes an Arbitrum One archive node as a reference:

```terraform
resource "google_compute_instance" "arbitrum_one" {
  name         = "arbitrum-one-archive-node"
  machine_type = "n1-highmem-4"  # 4 vCPUs, 26GB RAM
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
    }
  }

  attached_disk {
    source      = local.arbitrum_one_disk_name
    mode        = "READ_WRITE"
    device_name = "arbitrum-mainnet"
  }

  can_ip_forward = true
  # ... additional configuration
}
```

### Step 2: Create VM Instance Resource

Add a new `google_compute_instance` resource to `main.tf` based on your chain's requirements:

1. **Define local variables** for disk names and startup scripts
2. **Create the disk resource** with appropriate size
3. **Configure the VM instance** with proper machine type and network settings
4. **Set up service account** for proper permissions

### Step 3: Deploy Infrastructure

Navigate to the infrastructure directory and apply changes:

```bash
cd private-ops/infrastructure/archive-nodes
terraform plan
# Review the planned changes carefully
terraform apply
```

⚠️ **Important**: Always run `terraform plan` first and carefully review the changes before applying.

### Step 4: Configure Tailscale Networking

After the instance is created, you need to connect it to the Tailscale network for secure access.

#### Get Tailscale Login URL

Run this command to retrieve the Tailscale authentication URL from the instance's startup logs:

```bash
gcloud compute instances get-serial-port-output $NODE_NAME | grep "login.tailscale"
```

Replace `$NODE_NAME` with your actual instance name (e.g., `arbitrum-one-archive-node`).

#### Complete Tailscale Setup

1. **Open the authentication URL** in your browser
2. **Authenticate** using your Tailscale account
3. **Verify the instance appears** in the Tailscale admin panel
4. **Test SSH access** using your Tailscale user or root

The startup script automatically configures:

- Route advertisement for the subnet (`10.1.0.0/24`)
- SSH access through Tailscale
- DNS settings

### Step 5: Configure Storage

#### Mount the Attached Disk

SSH into the instance as root and mount the attached disk for blockchain data.

📖 **Reference**: Follow the detailed [Google Cloud disk formatting guide](https://cloud.google.com/compute/docs/disks/format-mount-disk-linux#format_linux) for complete instructions.

## Next Steps

After setting up your archive node:

1. **Configure monitoring** and alerting
2. **Document node-specific configuration** for your team
3. **Integrate with existing OSO infrastructure** (Dagster assets)

For additional support, reach out to the OSO team through [Discord](https://www.opensource.observer/discord).
