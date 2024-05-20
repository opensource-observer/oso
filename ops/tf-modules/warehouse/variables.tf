variable "name" {
  type        = string
  description = "The name to use for this warehouse"
}

variable "dataset_name" {
  type        = string
  default     = "Open Source Observer Dataset"
  description = "The name of the publicly available dataset"
}

variable "dataset_description" {
  type        = string
  default     = "Open Source Observer's Publicly Available Dataset"
  description = "The name of the publicly available dataset"
}

variable "dataset_location" {
  type        = string
  default     = "US"
  description = "The location for the dataset"
}

variable "environment" {
  type        = string
  description = "The environment"
}

variable "cloudsql_name" {
  type        = string
  description = "CloudSQL instance name"
}

variable "additional_cloudsql_client_principals" {
  type        = list(string)
  description = "List of principals to give client access to the cloudsql instance"
  default     = []
}

variable "bucket_rw_principals" {
  type        = list(string)
  description = "List of principals to give rw on our data transfer bucket"
  default     = []
}

variable "additional_bucket_rw_service_account_names" {
  type        = list(string)
  description = "List of names to use for new service accounts with rw access"
  default     = []
}

variable "cloudsql_db_name" {
  type        = string
  default     = "postgres"
  description = "CloudSQL DB Name"
}

variable "cloudsql_postgres_version" {
  type        = string
  description = "CloudSQL Postgres Version"
  default     = "POSTGRES_15"
}

variable "cloudsql_tier" {
  type        = string
  description = "The cloudsql tier to deploy"
}

variable "cloudsql_zone" {
  type        = string
  description = "The cloudsql zone"
}

variable "cloudsql_deletion_protection_enabled" {
  type    = bool
  default = false
}

variable "cloudsql_ip_configuration" {
  type = object({
    authorized_networks                           = optional(list(map(string)), [])
    ipv4_enabled                                  = optional(bool, true)
    private_network                               = optional(string)
    require_ssl                                   = optional(bool)
    ssl_mode                                      = optional(string)
    allocated_ip_range                            = optional(string)
    enable_private_path_for_google_cloud_services = optional(bool, false)
    psc_enabled                                   = optional(bool, false)
    psc_allowed_consumer_projects                 = optional(list(string), [])
  })
  default = {}
}
