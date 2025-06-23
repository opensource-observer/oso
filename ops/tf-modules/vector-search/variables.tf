variable "bucket_name" {
  description = "The name of the GCS bucket where the vector search data will be stored."
  type        = string
}

variable "name_prefix" {
  description = "The prefix for names to be created for vector search components."
  type        = string
}

variable "index_description" {
  description = "A description for the vector search index."
  type        = string
  default     = "A vector search index for storing and querying embeddings."
}

variable "labels" {
  description = "Labels to apply to the vector search index."
  type        = map(string)
  default     = {}
  
}

variable "project_id" {
  description = "The ID of the Google Cloud project where the resources will be created."
  type        = string
}

variable "region" {
  description = "The region where the resources will be created."
  type        = string
}

variable "index_update_method" {
  description = "The method to use for updating the index. Options are 'batch' or 'streaming'."
  type        = string
  default     = "BATCH_UPDATE"
}

variable "gcp_network" {
  description = "The name of the GCP network to use for the vector search service."
  type        = string
}

variable "shard_size" {
  description = "The size of the shards for the index. Options are 'SHARD_SIZE_SMALL', 'SHARD_SIZE_MEDIUM', or 'SHARD_SIZE_LARGE'."
  type        = string
  default     = "SHARD_SIZE_SMALL"
}

variable "dimensions" {
  description = "The number of dimensions for the embeddings in the index."
  type        = number
  default     = 768
  
}

variable "approximate_neighbors_count" {
  description = "The number of approximate neighbors to return for each query."
  type        = number
  default     = 150
}

variable "distance_measure_type" {
  description = "The type of distance measure to use for the index. Options are 'DOT_PRODUCT_DISTANCE' or 'COSINE_DISTANCE'."
  type        = string
  default     = "DOT_PRODUCT_DISTANCE"  
}