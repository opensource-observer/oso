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

variable "cloudsql_databases" {
  type = list(object({
    name                = string
    database_version    = string
    tier                = string
    zone                = string
    user_name           = string
    deletion_protection = bool
    additional_databases = list(object({
      name      = string
      charset   = string
      collation = string
    }))
    additional_users = list(object({
      name            = string
      password        = string
      random_password = bool
    }))
    ip_configuration = object({
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
  }))
  description = "List of CloudSQL databases with their configurations"
  default     = []
}
