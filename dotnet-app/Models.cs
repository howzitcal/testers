using System.Text.Json;
using MySqlConnector;

namespace DotnetLeads;

public record Lead(long Id, string Name, string Email, string Status);

public record BackgroundJob(long Id, string JobType, string Payload, string Status);

public static class Models
{
    public static readonly string[] Statuses = ["new", "contacted", "qualified"];
    public const string JobWelcomeEmail = "welcome_email";

    public static async Task<List<Lead>> ListLeadsAsync(MySqlDataSource ds)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT id, name, email, status FROM leads ORDER BY id";
        await using var reader = await cmd.ExecuteReaderAsync();
        var leads = new List<Lead>();
        while (await reader.ReadAsync())
        {
            leads.Add(new Lead(
                reader.GetInt64(0),
                reader.GetString(1),
                reader.GetString(2),
                reader.GetString(3)));
        }
        return leads;
    }

    public static async Task<Lead?> GetLeadAsync(MySqlDataSource ds, long id)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT id, name, email, status FROM leads WHERE id = @id";
        cmd.Parameters.AddWithValue("@id", id);
        await using var reader = await cmd.ExecuteReaderAsync();
        if (!await reader.ReadAsync()) return null;
        return new Lead(
            reader.GetInt64(0),
            reader.GetString(1),
            reader.GetString(2),
            reader.GetString(3));
    }

    public static async Task<Lead> CreateLeadAsync(MySqlDataSource ds, string name, string email, string status)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "INSERT INTO leads (name, email, status) VALUES (@n, @e, @s); SELECT LAST_INSERT_ID();";
        cmd.Parameters.AddWithValue("@n", name);
        cmd.Parameters.AddWithValue("@e", email);
        cmd.Parameters.AddWithValue("@s", status);
        var id = Convert.ToInt64(await cmd.ExecuteScalarAsync());
        return (await GetLeadAsync(ds, id))!;
    }

    public static async Task UpdateLeadAsync(MySqlDataSource ds, long id, string name, string email, string status)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "UPDATE leads SET name = @n, email = @e, status = @s WHERE id = @id";
        cmd.Parameters.AddWithValue("@n", name);
        cmd.Parameters.AddWithValue("@e", email);
        cmd.Parameters.AddWithValue("@s", status);
        cmd.Parameters.AddWithValue("@id", id);
        await cmd.ExecuteNonQueryAsync();
    }

    public static async Task DeleteLeadAsync(MySqlDataSource ds, long id)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "DELETE FROM leads WHERE id = @id";
        cmd.Parameters.AddWithValue("@id", id);
        await cmd.ExecuteNonQueryAsync();
    }

    public static async Task<long> CountLeadsAsync(MySqlDataSource ds)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM leads";
        return Convert.ToInt64(await cmd.ExecuteScalarAsync());
    }

    public static async Task CreateAuditLogAsync(MySqlDataSource ds, string message)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText = "INSERT INTO audit_log (message) VALUES (@m)";
        cmd.Parameters.AddWithValue("@m", message);
        await cmd.ExecuteNonQueryAsync();
    }

    public static async Task EnqueueWelcomeEmailAsync(MySqlDataSource ds, long leadId, string name, string email)
    {
        var payload = JsonSerializer.Serialize(new { lead_id = leadId, name, email });
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText =
            "INSERT INTO background_jobs (job_type, payload, status) VALUES (@t, @p, 'pending')";
        cmd.Parameters.AddWithValue("@t", JobWelcomeEmail);
        cmd.Parameters.AddWithValue("@p", payload);
        await cmd.ExecuteNonQueryAsync();
    }

    public static async Task<BackgroundJob?> ClaimNextJobAsync(MySqlDataSource ds)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var tx = await conn.BeginTransactionAsync();
        await using var select = conn.CreateCommand();
        select.Transaction = tx;
        select.CommandText = """
            SELECT id, job_type, payload, status
            FROM background_jobs
            WHERE status = 'pending'
            ORDER BY id
            LIMIT 1
            FOR UPDATE
            """;
        await using var reader = await select.ExecuteReaderAsync();
        if (!await reader.ReadAsync())
        {
            await reader.DisposeAsync();
            await tx.RollbackAsync();
            return null;
        }
        var job = new BackgroundJob(
            reader.GetInt64(0),
            reader.GetString(1),
            reader.GetString(2),
            reader.GetString(3));
        await reader.DisposeAsync();

        await using var update = conn.CreateCommand();
        update.Transaction = tx;
        update.CommandText =
            "UPDATE background_jobs SET status = 'running', started_at = UTC_TIMESTAMP(6) WHERE id = @id";
        update.Parameters.AddWithValue("@id", job.Id);
        await update.ExecuteNonQueryAsync();
        await tx.CommitAsync();
        return job with { Status = "running" };
    }

    public static async Task MarkJobDoneAsync(MySqlDataSource ds, long id)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText =
            "UPDATE background_jobs SET status = 'done', finished_at = UTC_TIMESTAMP(6) WHERE id = @id";
        cmd.Parameters.AddWithValue("@id", id);
        await cmd.ExecuteNonQueryAsync();
    }

    public static async Task MarkJobFailedAsync(MySqlDataSource ds, long id, string error)
    {
        await using var conn = await ds.OpenConnectionAsync();
        await using var cmd = conn.CreateCommand();
        cmd.CommandText =
            "UPDATE background_jobs SET status = 'failed', error = @e, finished_at = UTC_TIMESTAMP(6) WHERE id = @id";
        cmd.Parameters.AddWithValue("@e", error);
        cmd.Parameters.AddWithValue("@id", id);
        await cmd.ExecuteNonQueryAsync();
    }
}
