use sqlx::mysql::MySqlPoolOptions;
use sqlx::{MySql, Pool};
use tokio::time::{sleep, Duration};

use crate::config::Config;

pub type Db = Pool<MySql>;

pub async fn ensure_database(cfg: &Config) -> Result<(), sqlx::Error> {
    let mut last_err = None;
    for attempt in 1..=30 {
        match MySqlPoolOptions::new()
            .max_connections(1)
            .connect(&cfg.server_url())
            .await
        {
            Ok(pool) => {
                let q = format!(
                    "CREATE DATABASE IF NOT EXISTS `{}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
                    cfg.db_name
                );
                sqlx::query(&q).execute(&pool).await?;
                pool.close().await;
                tracing::info!("MySQL ready; database `{}` ensured", cfg.db_name);
                return Ok(());
            }
            Err(err) => {
                tracing::info!("Waiting for MySQL ({attempt}/30): {err}");
                last_err = Some(err);
                sleep(Duration::from_secs(2)).await;
            }
        }
    }
    Err(last_err.expect("ensure_database failed"))
}

pub async fn open_pool(cfg: &Config) -> Result<Db, sqlx::Error> {
    MySqlPoolOptions::new()
        .max_connections(10)
        .connect(&cfg.database_url())
        .await
}

pub async fn migrate(pool: &Db) -> Result<(), sqlx::Error> {
    sqlx::query(
        r#"CREATE TABLE IF NOT EXISTS leads (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            email VARCHAR(200) NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'new',
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"#,
    )
    .execute(pool)
    .await?;

    sqlx::query(
        r#"CREATE TABLE IF NOT EXISTS audit_log (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            message VARCHAR(1000) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"#,
    )
    .execute(pool)
    .await?;

    sqlx::query(
        r#"CREATE TABLE IF NOT EXISTS background_jobs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            job_type VARCHAR(100) NOT NULL,
            payload TEXT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            started_at DATETIME(6) NULL,
            finished_at DATETIME(6) NULL,
            error TEXT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"#,
    )
    .execute(pool)
    .await?;

    Ok(())
}
