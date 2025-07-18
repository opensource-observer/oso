output "index_display_name" {
  description = "The display name of the created vector search index."
  value       = google_vertex_ai_index.index.display_name
}

output "endpoint_display_name" {
  description = "The display name of the created vector search index endpoint."
  value       = google_vertex_ai_index_endpoint.vertex_index_endpoint_deployed.display_name
}

output "deployed_index_display_name" {
  description = "The display name of the deployed vector search index."
  value       = google_vertex_ai_index_endpoint_deployed_index.deployed_index.name
}