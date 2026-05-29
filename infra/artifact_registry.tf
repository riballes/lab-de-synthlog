import {
  to = google_artifact_registry_repository.synthlog
  id = "projects/${var.project_id}/locations/${var.region}/repositories/synthlog"
}

resource "google_artifact_registry_repository" "synthlog" {
  repository_id = "synthlog"
  location      = var.region
  format        = "DOCKER"
  description   = "Docker images for synthlog synthetic log generator"
}

locals {
  image_uri = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.synthlog.repository_id}/synthlog:${var.image_tag}"
}
