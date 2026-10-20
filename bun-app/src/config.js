/** Mirrors Django/Go/Deno DB_* env vars for the shared MySQL. */

function getenv(key, fallback) {
  return Bun.env[key] || fallback;
}

export function loadConfig() {
  return {
    dbHost: getenv("DB_HOST", "host.docker.internal"),
    dbPort: Number(getenv("DB_PORT", "3306")),
    dbUsername: getenv("DB_USERNAME", "root"),
    dbPassword: getenv("DB_PASSWORD", "password"),
    dbName: getenv("DB_NAME", "bun_leads"),
    httpPort: Number(getenv("HTTP_PORT", "8005")),
  };
}
