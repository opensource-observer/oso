variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "cluster_name" {
  type        = string
  description = "Name for the gke cluster"
}

variable "dagster_bucket_prefix" {
  type = string
}

variable "dagster_bucket_location" {
  type    = string
  default = "US"
}

variable "dagster_bucket_rw_principals" {
  type        = list(string)
  description = "List of principals to give rw on our data transfer bucket"
  default     = []
}

variable "default_node_pool_cluster_zones" {
  type        = list(string)
  description = "The default node pool is intended to be standard vms (non-volatile). This should be a smaller set of cluster zones"
  default     = ["us-central1-a"]
}

variable "cluster_region" {
  type        = string
  description = "The region for the gke cluster"
  default     = "us-central1"
}

variable "cluster_zones" {
  type        = list(string)
  description = "The zones for the gke cluster"
  default     = ["us-central1-a", "us-central1-b", "us-central1-c"]
}

variable "enable_http_load_balancing" {
  type        = bool
  description = "http loadbalancing"
  default     = true
}

variable "main_subnet_cidr" {
  type        = string
  description = "The ip_range for services"
  default     = "10.0.0.0/16"
}

variable "extra_node_pools" {
  type        = list(map(any))
  description = "Extra node pools to add"
  default     = []
}

variable "extra_node_labels" {
  type        = map(any)
  description = "Extra node pools to add"
  default     = {}
}

variable "extra_node_metadata" {
  type        = map(any)
  description = "Extra node pools to add"
  default     = {}
}

variable "extra_node_taints" {
  type        = map(any)
  description = "Extra node taints to add"
  default     = {}
}

variable "extra_node_tags" {
  type        = map(any)
  description = "Extra node tags to add"
  default     = {}
}

variable "extra_pool_oauth_scopes" {
  type        = map(any)
  description = "Extra node oauth scopes"
  default     = {}
}

variable "pods_cidr" {
  type        = string
  description = "The CIDR for the pods"
}

variable "services_cidr" {
  type        = string
  description = "The CIDR for the services"
}
