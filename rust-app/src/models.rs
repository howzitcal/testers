use serde::{Deserialize, Serialize};
use sqlx::FromRow;

use crate::db::Db;

pub const STATUSES: &[&str] = &["new", "contacted", "qualified"];
pub const JOB_WELCOME_EMAIL: &str = "welcome_email";

#[derive(Debug, Clone, FromRow, Serialize)]
pub struct Lead {
    pub id: i64,
    pub name: String,
    pub email: String,
    pub status: String,
}

#[derive(Debug, Clone, FromRow)]
pub struct BackgroundJob {
    pub id: i64,
    pub job_type: String,
    pub payload: String,
    #[allow(dead_code)]
    pub status: String,
}

#[derive(Debug, Deserialize)]
pub struct WelcomePayload {
    pub lead_id: i64,
    pub name: String,
    pub email: String,
}

pub async fn list_leads(pool: &Db) -> Result<Vec<Lead>, sqlx::Error> {
    sqlx::query_as::<_, Lead>(
        "SELECT id, name, email, status FROM leads ORDER BY id",
    )
    .fetch_all(pool)
    .await
}

pub async fn get_lead(pool: &Db, id: i64) -> Result<Option<Lead>, sqlx::Error> {
    sqlx::query_as::<_, Lead>("SELECT id, name, email, status FROM leads WHERE id = ?")
        .bind(id)
        .fetch_optional(pool)
        .await
}

pub async fn create_lead(
    pool: &Db,
    name: &str,
    email: &str,
    status: &str,
) -> Result<Lead, sqlx::Error> {
    let result = sqlx::query("INSERT INTO leads (name, email, status) VALUES (?, ?, ?)")
        .bind(name)
        .bind(email)
        .bind(status)
        .execute(pool)
        .await?;
    let id = result.last_insert_id() as i64;
    get_lead(pool, id)
        .await?
        .ok_or_else(|| sqlx::Error::RowNotFound)
}

pub async fn update_lead(
    pool: &Db,
    id: i64,
    name: &str,
    email: &str,
    status: &str,
) -> Result<(), sqlx::Error> {
    sqlx::query("UPDATE leads SET name = ?, email = ?, status = ? WHERE id = ?")
        .bind(name)
        .bind(email)
        .bind(status)
        .bind(id)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn delete_lead(pool: &Db, id: i64) -> Result<(), sqlx::Error> {
    sqlx::query("DELETE FROM leads WHERE id = ?")
        .bind(id)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn count_leads(pool: &Db) -> Result<i64, sqlx::Error> {
    let (n,): (i64,) = sqlx::query_as("SELECT COUNT(*) FROM leads")
        .fetch_one(pool)
        .await?;
    Ok(n)
}

pub async fn create_audit_log(pool: &Db, message: &str) -> Result<(), sqlx::Error> {
    sqlx::query("INSERT INTO audit_log (message) VALUES (?)")
        .bind(message)
        .execute(pool)
        .await?;
    Ok(())
}

pub async fn enqueue_welcome_email(
    pool: &Db,
    lead_id: i64,
    name: &str,
    email: &str,
) -> Result<(), sqlx::Error> {
    let payload = serde_json::json!({
        "lead_id": lead_id,
        "name": name,
        "email": email,
    })
    .to_string();
    sqlx::query(
        "INSERT INTO background_jobs (job_type, payload, status) VALUES (?, ?, 'pending')",
    )
    .bind(JOB_WELCOME_EMAIL)
    .bind(payload)
    .execute(pool)
    .await?;
    Ok(())
}

pub async fn claim_next_job(pool: &Db) -> Result<Option<BackgroundJob>, sqlx::Error> {
    let mut tx = pool.begin().await?;
    let job = sqlx::query_as::<_, BackgroundJob>(
        r#"SELECT id, job_type, payload, status
           FROM background_jobs
           WHERE status = 'pending'
           ORDER BY id
           LIMIT 1
           FOR UPDATE"#,
    )
    .fetch_optional(&mut *tx)
    .await?;

    let Some(job) = job else {
        tx.rollback().await?;
        return Ok(None);
    };

    sqlx::query(
        "UPDATE background_jobs SET status = 'running', started_at = UTC_TIMESTAMP(6) WHERE id = ?",
    )
    .bind(job.id)
    .execute(&mut *tx)
    .await?;
    tx.commit().await?;

    Ok(Some(BackgroundJob {
        status: "running".into(),
        ..job
    }))
}

pub async fn mark_job_done(pool: &Db, id: i64) -> Result<(), sqlx::Error> {
    sqlx::query(
        "UPDATE background_jobs SET status = 'done', finished_at = UTC_TIMESTAMP(6) WHERE id = ?",
    )
    .bind(id)
    .execute(pool)
    .await?;
    Ok(())
}

pub async fn mark_job_failed(pool: &Db, id: i64, error: &str) -> Result<(), sqlx::Error> {
    sqlx::query(
        "UPDATE background_jobs SET status = 'failed', error = ?, finished_at = UTC_TIMESTAMP(6) WHERE id = ?",
    )
    .bind(error)
    .bind(id)
    .execute(pool)
    .await?;
    Ok(())
}
