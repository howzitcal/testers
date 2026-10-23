mod config;
mod db;
mod handlers;
mod mail;
mod models;
mod templates;
mod worker;

use std::net::SocketAddr;

use tracing_subscriber::FmtSubscriber;

use crate::config::Config;
use crate::handlers::AppState;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    FmtSubscriber::builder()
        .with_max_level(tracing::Level::INFO)
        .init();

    let cmd = std::env::args().nth(1).unwrap_or_default();
    if cmd != "web" && cmd != "worker" {
        eprintln!("usage: leads <web|worker>");
        std::process::exit(1);
    }

    let cfg = Config::load();
    db::ensure_database(&cfg).await?;
    let pool = db::open_pool(&cfg).await?;
    db::migrate(&pool).await?;

    match cmd.as_str() {
        "web" => {
            let app = handlers::router(AppState { db: pool });
            let addr = SocketAddr::from(([0, 0, 0, 0], cfg.http_port));
            tracing::info!("Rust leads web listening on {addr}");
            let listener = tokio::net::TcpListener::bind(addr).await?;
            axum::serve(listener, app).await?;
        }
        "worker" => worker::run(pool).await,
        _ => unreachable!(),
    }
    Ok(())
}
