/** Mirrors Django/Go DB_* env vars for the shared MySQL. */

export type Config = {
  dbHost: string;
  dbPort: number;
  dbUsername: string;
  dbPassword: string;
  dbName: string;
  httpPort: number;
};

function getenv(key: string, fallback: string): string {
  return Deno.env.get(key) || fallback;
}

export function loadConfig(): Config {
  return {
    dbHost: getenv("DB_HOST", "host.docker.internal"),
    dbPort: Number(getenv("DB_PORT", "3306")),
    dbUsername: getenv("DB_USERNAME", "root"),
    dbPassword: getenv("DB_PASSWORD", "password"),
    dbName: getenv("DB_NAME", "deno_leads"),
    httpPort: Number(getenv("HTTP_PORT", "8004")),
  };
}
