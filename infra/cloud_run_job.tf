resource "google_cloud_run_v2_job" "synthlog" {
  name     = "synthlog-generator"
  location = var.region

  template {
    template {
      service_account = google_service_account.synthlog.email
      timeout         = var.job_timeout

      containers {
        image = local.image_uri

        args = concat(
          ["generate"],
          ["--seed", tostring(var.synthlog_seed)],
          ["--users", tostring(var.synthlog_users)],
          ["--duration", tostring(var.synthlog_duration_hours)],
          ["--emitter", var.synthlog_emitter],
          var.synthlog_scenarios != "" ? flatten([
            for s in split(",", var.synthlog_scenarios) : ["--scenario", trimspace(s)]
          ]) : [],
        )

        resources {
          limits = {
            memory = var.job_memory
            cpu    = var.job_cpu
          }
        }

        env {
          name  = "SYNTHLOG_SEED"
          value = tostring(var.synthlog_seed)
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [
      launch_stage,
    ]
  }
}
