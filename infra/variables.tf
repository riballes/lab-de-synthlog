variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run and Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag to deploy (e.g., latest, v0.1.0, sha-abc123)"
  type        = string
  default     = "latest"
}

variable "synthlog_seed" {
  description = "Random seed for deterministic output"
  type        = number
  default     = 42
}

variable "synthlog_users" {
  description = "Number of synthetic users"
  type        = number
  default     = 5
}

variable "synthlog_duration_hours" {
  description = "Hours of simulated time per run"
  type        = number
  default     = 8
}

variable "synthlog_emitter" {
  description = "Emitter to use (jsonl, console, or external plugin name)"
  type        = string
  default     = "jsonl"
}

variable "synthlog_scenarios" {
  description = "Comma-separated list of scenario names"
  type        = string
  default     = ""
}

variable "scheduler_cron" {
  description = "Cloud Scheduler cron expression (empty to disable)"
  type        = string
  default     = ""
}

variable "scheduler_timezone" {
  description = "Timezone for Cloud Scheduler"
  type        = string
  default     = "America/Los_Angeles"
}

variable "job_memory" {
  description = "Memory limit for Cloud Run Job"
  type        = string
  default     = "512Mi"
}

variable "job_cpu" {
  description = "CPU limit for Cloud Run Job"
  type        = string
  default     = "1"
}

variable "job_timeout" {
  description = "Max execution time for Cloud Run Job"
  type        = string
  default     = "3600s"
}
