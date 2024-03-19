variable "project_name" {
  type        = string
  description = "The name to use for the project"
}

variable "organization_id" {
  type        = string
  description = "The org id"
}

variable "admin_principals" {
  type        = list(string)
  description = "A list of gcp princpals that have admin privileges on this project"
}
