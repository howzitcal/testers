import mysql from "mysql2/promise";

export async function ensureDatabase(cfg) {
  let lastErr;
  for (let attempt = 1; attempt <= 30; attempt++) {
    try {
      const conn = await mysql.createConnection({
        host: cfg.dbHost,
        port: cfg.dbPort,
        user: cfg.dbUsername,
        password: cfg.dbPassword,
      });
      await conn.query(
        `CREATE DATABASE IF NOT EXISTS \`${cfg.dbName}\` ` +
          `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`,
      );
      await conn.end();
      console.log(`MySQL ready; database \`${cfg.dbName}\` ensured`);
      return;
    } catch (err) {
      lastErr = err;
      console.log(`Waiting for MySQL (${attempt}/30): ${err}`);
      await Bun.sleep(2000);
    }
  }
  throw new Error(`Could not connect to MySQL: ${lastErr}`);
}

export function openPool(cfg) {
  return mysql.createPool({
    host: cfg.dbHost,
    port: cfg.dbPort,
    user: cfg.dbUsername,
    password: cfg.dbPassword,
    database: cfg.dbName,
    waitForConnections: true,
    connectionLimit: 10,
    charset: "utf8mb4",
  });
}

export async function migrate(pool) {
  const stmts = [
    `CREATE TABLE IF NOT EXISTS leads (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(200) NOT NULL,
      email VARCHAR(200) NOT NULL,
      status VARCHAR(50) NOT NULL DEFAULT 'new',
      created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
    `CREATE TABLE IF NOT EXISTS audit_log (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
      message VARCHAR(1000) NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
    `CREATE TABLE IF NOT EXISTS background_jobs (
      id BIGINT AUTO_INCREMENT PRIMARY KEY,
      job_type VARCHAR(100) NOT NULL,
      payload TEXT NOT NULL,
      status VARCHAR(20) NOT NULL DEFAULT 'pending',
      created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
      started_at DATETIME(6) NULL,
      finished_at DATETIME(6) NULL,
      error TEXT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
  ];
  for (const s of stmts) {
    await pool.query(s);
  }
}
