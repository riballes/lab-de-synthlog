# Optional: Cloud Scheduler trigger for periodic execution
# Set var.scheduler_cron to a cron expression to enable (e.g., "0 8 * * 1-5")

resource "google_cloud_scheduler_job" "synthlog" {
  count = var.scheduler_cron != "" ? 1 : 0

  name        = "synthlog-trigger"
  description = "Triggers synthlog Cloud Run Job on schedule"
  schedule    = var.scheduler_cron
  time_zone   = var.scheduler_timezone
  region      = var.region

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.synthlog.name}:run"

    oauth_token {
      service_account_email = google_service_account.synthlog.email
    }
  }
}

# Grant scheduler SA permission to invoke the job
resource "google_project_iam_member" "scheduler_run_invoker" {
  count = var.scheduler_cron != "" ? 1 : 0

  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.synthlog.email}"
}
