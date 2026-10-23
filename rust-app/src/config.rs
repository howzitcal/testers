use std::env;

#[derive(Clone, Debug)]
pub struct Config {
    pub db_host: String,
    pub db_port: u16,
    pub db_username: String,
    pub db_password: String,
    pub db_name: String,
    pub http_port: u16,
}

impl Config {
    pub fn load() -> Self {
        Self {
            db_host: getenv("DB_HOST", "host.docker.internal"),
            db_port: getenv("DB_PORT", "3306").parse().unwrap_or(3306),
            db_username: getenv("DB_USERNAME", "root"),
            db_password: getenv("DB_PASSWORD", "password"),
            db_name: getenv("DB_NAME", "rust_leads"),
            http_port: getenv("HTTP_PORT", "8006").parse().unwrap_or(8006),
        }
    }

    pub fn database_url(&self) -> String {
        format!(
            "mysql://{}:{}@{}:{}/{}",
            self.db_username, self.db_password, self.db_host, self.db_port, self.db_name
        )
    }

    pub fn server_url(&self) -> String {
        format!(
            "mysql://{}:{}@{}:{}",
            self.db_username, self.db_password, self.db_host, self.db_port
        )
    }
}

fn getenv(key: &str, fallback: &str) -> String {
    env::var(key).unwrap_or_else(|_| fallback.to_string())
}
