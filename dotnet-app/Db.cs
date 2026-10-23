using MySqlConnector;

namespace DotnetLeads;

public static class Db
{
    public static async Task EnsureDatabaseAsync(Config cfg)
    {
        Exception? last = null;
        for (var attempt = 1; attempt <= 30; attempt++)
        {
            try
            {
                await using var conn = new MySqlConnection(cfg.ServerConnectionString);
                await conn.OpenAsync();
                await using var cmd = conn.CreateCommand();
                cmd.CommandText =
                    $"CREATE DATABASE IF NOT EXISTS `{cfg.DbName}` " +
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci";
                await cmd.ExecuteNonQueryAsync();
                Console.WriteLine($"MySQL ready; database `{cfg.DbName}` ensured");
                return;
            }
            catch (Exception ex)
            {
                last = ex;
                Console.WriteLine($"Waiting for MySQL ({attempt}/30): {ex.Message}");
                await Task.Delay(2000);
            }
        }
        throw new Exception("Could not connect to MySQL", last);
    }

    public static MySqlDataSource Open(Config cfg) => new(cfg.ConnectionString);

    public static async Task MigrateAsync(MySqlDataSource ds)
    {
        await using var conn = await ds.OpenConnectionAsync();
        foreach (var sql in new[]
        {
            """
            CREATE TABLE IF NOT EXISTS leads (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              name VARCHAR(200) NOT NULL,
              email VARCHAR(200) NOT NULL,
              status VARCHAR(50) NOT NULL DEFAULT 'new',
              created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_log (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
              message VARCHAR(1000) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
            """
            CREATE TABLE IF NOT EXISTS background_jobs (
              id BIGINT AUTO_INCREMENT PRIMARY KEY,
              job_type VARCHAR(100) NOT NULL,
              payload TEXT NOT NULL,
              status VARCHAR(20) NOT NULL DEFAULT 'pending',
              created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
              started_at DATETIME(6) NULL,
              finished_at DATETIME(6) NULL,
              error TEXT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """,
        })
        {
            await using var cmd = conn.CreateCommand();
            cmd.CommandText = sql;
            await cmd.ExecuteNonQueryAsync();
        }
    }
}
