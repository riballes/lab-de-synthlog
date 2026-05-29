output "artifact_registry_repo" {
  description = "Artifact Registry repository URI"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.synthlog.repository_id}"
}

output "image_uri" {
  description = "Full image URI for the deployed synthlog container"
  value       = local.image_uri
}

output "cloud_run_job_name" {
  description = "Cloud Run Job name"
  value       = google_cloud_run_v2_job.synthlog.name
}

output "service_account_email" {
  description = "Service account email used by the job"
  value       = google_service_account.synthlog.email
}
