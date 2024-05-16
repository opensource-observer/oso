output "gke_endpoint" {
  value = module.gke.endpoint
}

output "gke_ca_certificate" {
  value = module.gke.ca_certificate
}

output "gke_identity_namespace" {
  value = module.gke.identity_namespace
}
