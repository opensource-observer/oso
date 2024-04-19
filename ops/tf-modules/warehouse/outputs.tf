output "dataset_id" {
  value = google_bigquery_dataset.dataset.id
}

output "metadata_user_temp_password" {
  value = random_password.metadata_user_temp_password.result
}
