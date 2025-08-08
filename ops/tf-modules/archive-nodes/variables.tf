variable "project_id" {
  description = "The ID of the Google Cloud project where the resources will be created."
  type        = string
}

variable "region" {
  description = "The region where the resources will be created."
  type        = string
}

variable "zone" {
  description = "The zone where the resources will be created."
  type        = string
}

variable "network_name" {
  description = "The name of the GCP network to use for the instance services."
  type        = string
}

variable "scripts_path" {
  description = "The path to the directory containing startup scripts."
  type        = string
  default     = "./scripts"
}
