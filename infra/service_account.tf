resource "google_service_account" "synthlog" {
  account_id   = "synthlog-runner"
  display_name = "Synthlog Cloud Run Job Runner"
  description  = "Service account for synthlog Cloud Run Job"
}

# Allow Cloud Run to use this service account
resource "google_project_iam_member" "synthlog_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.synthlog.email}"
}
