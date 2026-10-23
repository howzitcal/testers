use std::time::Duration;

use tokio::signal;
use tokio::time::{interval, sleep};

use crate::db::Db;
use crate::mail::send_mock_mail;
use crate::models::{
    claim_next_job, count_leads, create_audit_log, mark_job_done, mark_job_failed,
    WelcomePayload, JOB_WELCOME_EMAIL,
};

pub async fn run(pool: Db) {
    tracing::info!("Rust worker started (MySQL queue + schedules every 1s)");

    let sched_pool = pool.clone();
    let mut sched = interval(Duration::from_secs(1));
    let schedule_task = tokio::spawn(async move {
        loop {
            sched.tick().await;
            run_health_check(&sched_pool).await;
            dummy_job();
        }
    });

    loop {
        tokio::select! {
            _ = signal::ctrl_c() => {
                schedule_task.abort();
                tracing::info!("Rust worker stopped");
                break;
            }
            result = claim_next_job(&pool) => {
                match result {
                    Ok(None) => sleep(Duration::from_secs(1)).await,
                    Ok(Some(job)) => {
                        if let Err(err) = handle_job(&job).await {
                            tracing::error!("Job id={} failed: {err}", job.id);
                            let _ = mark_job_failed(&pool, job.id, &err.to_string()).await;
                        } else if let Err(err) = mark_job_done(&pool, job.id).await {
                            tracing::error!("mark done id={}: {err}", job.id);
                        }
                    }
                    Err(err) => {
                        tracing::error!("claim job: {err}");
                        sleep(Duration::from_secs(1)).await;
                    }
                }
            }
        }
    }
}

async fn handle_job(job: &crate::models::BackgroundJob) -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    if job.job_type != JOB_WELCOME_EMAIL {
        return Err(format!("unknown job_type: {}", job.job_type).into());
    }
    let payload: WelcomePayload = serde_json::from_str(&job.payload)?;
    tracing::info!(
        "Processing welcome_email job id={} lead_id={}",
        job.id,
        payload.lead_id
    );
    sleep(Duration::from_millis(500)).await;
    send_mock_mail(
        &payload.name,
        &payload.email,
        "Welcome!",
        &format!("Thanks for signing up, {}.", payload.name),
    );
    Ok(())
}

async fn run_health_check(pool: &Db) {
    match count_leads(pool).await {
        Ok(n) => {
            let msg = format!("System health check OK — lead count={n}");
            if let Err(err) = create_audit_log(pool, &msg).await {
                tracing::error!("health check audit: {err}");
                return;
            }
            tracing::info!("{msg}");
        }
        Err(err) => tracing::error!("health check count: {err}"),
    }
}

fn dummy_job() {
    tracing::info!("dummy job");
}
