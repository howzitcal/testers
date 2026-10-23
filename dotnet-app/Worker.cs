using System.Text.Json;
using MySqlConnector;

namespace DotnetLeads;

public static class Worker
{
    public static async Task RunAsync(MySqlDataSource ds, CancellationToken ct)
    {
        Console.WriteLine(".NET worker started (MySQL queue + schedules every 1s)");

        using var schedule = new PeriodicTimer(TimeSpan.FromSeconds(1));
        var scheduleTask = Task.Run(async () =>
        {
            while (await schedule.WaitForNextTickAsync(ct))
            {
                await RunHealthCheckAsync(ds);
                DummyJob();
            }
        }, ct);

        try
        {
            while (!ct.IsCancellationRequested)
            {
                try
                {
                    var job = await Models.ClaimNextJobAsync(ds);
                    if (job is null)
                    {
                        await Task.Delay(1000, ct);
                        continue;
                    }

                    try
                    {
                        await HandleJobAsync(job);
                        await Models.MarkJobDoneAsync(ds, job.Id);
                    }
                    catch (Exception ex)
                    {
                        Console.Error.WriteLine($"Job id={job.Id} failed: {ex.Message}");
                        await Models.MarkJobFailedAsync(ds, job.Id, ex.Message);
                    }
                }
                catch (OperationCanceledException) when (ct.IsCancellationRequested)
                {
                    break;
                }
                catch (Exception ex)
                {
                    Console.Error.WriteLine($"claim job: {ex.Message}");
                    await Task.Delay(1000, ct);
                }
            }
        }
        finally
        {
            schedule.Dispose();
            try { await scheduleTask; } catch { /* ignore */ }
            Console.WriteLine(".NET worker stopped");
        }
    }

    private static async Task HandleJobAsync(BackgroundJob job)
    {
        if (job.JobType != Models.JobWelcomeEmail)
            throw new Exception($"unknown job_type: {job.JobType}");

        using var doc = JsonDocument.Parse(job.Payload);
        var root = doc.RootElement;
        var leadId = root.GetProperty("lead_id").GetInt64();
        var name = root.GetProperty("name").GetString() ?? "";
        var email = root.GetProperty("email").GetString() ?? "";

        Console.WriteLine($"Processing welcome_email job id={job.Id} lead_id={leadId}");
        await Task.Delay(500);
        Mail.SendMock(name, email, "Welcome!", $"Thanks for signing up, {name}.");
    }

    private static async Task RunHealthCheckAsync(MySqlDataSource ds)
    {
        try
        {
            var n = await Models.CountLeadsAsync(ds);
            var msg = $"System health check OK — lead count={n}";
            await Models.CreateAuditLogAsync(ds, msg);
            Console.WriteLine(msg);
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"health check: {ex.Message}");
        }
    }

    private static void DummyJob() => Console.WriteLine("dummy job");
}
