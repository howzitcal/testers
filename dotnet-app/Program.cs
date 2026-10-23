using DotnetLeads;
using MySqlConnector;

var cmd = args.ElementAtOrDefault(0);
if (cmd is not ("web" or "worker"))
{
    Console.Error.WriteLine("usage: DotnetLeads <web|worker>");
    return 1;
}

var cfg = Config.Load();
await Db.EnsureDatabaseAsync(cfg);
await using var ds = Db.Open(cfg);
await Db.MigrateAsync(ds);

if (cmd == "web")
{
    var builder = WebApplication.CreateBuilder(args);
    builder.WebHost.UseUrls($"http://0.0.0.0:{cfg.HttpPort}");
    var app = builder.Build();

    app.MapGet("/", async (HttpRequest req) =>
    {
        var leads = await Models.ListLeadsAsync(ds);
        var msg = req.Query["msg"].FirstOrDefault() ?? "";
        return Results.Content(Templates.RenderList(leads, msg), "text/html; charset=utf-8");
    });

    app.MapGet("/leads/new", () =>
        Results.Content(Templates.RenderForm("New Lead", "", "", "new"), "text/html; charset=utf-8"));

    app.MapPost("/leads/new", async (HttpRequest req) =>
    {
        var form = await req.ReadFormAsync();
        var name = (form["name"].FirstOrDefault() ?? "").Trim();
        var email = (form["email"].FirstOrDefault() ?? "").Trim();
        var status = (form["status"].FirstOrDefault() ?? "new").Trim();
        var errors = Validate(name, email, ref status);
        if (errors.Count > 0)
        {
            return Results.Content(
                Templates.RenderForm("New Lead", name, email, status, errors),
                "text/html; charset=utf-8");
        }
        var lead = await Models.CreateLeadAsync(ds, name, email, status);
        await Models.EnqueueWelcomeEmailAsync(ds, lead.Id, lead.Name, lead.Email);
        return Results.Redirect("/?msg=" + Uri.EscapeDataString("Lead created; welcome email queued."));
    });

    app.MapGet("/leads/{id:long}/edit", async (long id) =>
    {
        var lead = await Models.GetLeadAsync(ds, id);
        if (lead is null) return Results.NotFound("Not found");
        return Results.Content(
            Templates.RenderForm("Edit Lead", lead.Name, lead.Email, lead.Status),
            "text/html; charset=utf-8");
    });

    app.MapPost("/leads/{id:long}/edit", async (long id, HttpRequest req) =>
    {
        if (await Models.GetLeadAsync(ds, id) is null) return Results.NotFound("Not found");
        var form = await req.ReadFormAsync();
        var name = (form["name"].FirstOrDefault() ?? "").Trim();
        var email = (form["email"].FirstOrDefault() ?? "").Trim();
        var status = (form["status"].FirstOrDefault() ?? "new").Trim();
        var errors = Validate(name, email, ref status);
        if (errors.Count > 0)
        {
            return Results.Content(
                Templates.RenderForm("Edit Lead", name, email, status, errors),
                "text/html; charset=utf-8");
        }
        await Models.UpdateLeadAsync(ds, id, name, email, status);
        return Results.Redirect("/?msg=" + Uri.EscapeDataString("Lead updated."));
    });

    app.MapPost("/leads/{id:long}/delete", async (long id) =>
    {
        await Models.DeleteLeadAsync(ds, id);
        return Results.Redirect("/?msg=" + Uri.EscapeDataString("Lead deleted."));
    });

    Console.WriteLine($".NET leads web listening on :{cfg.HttpPort}");
    await app.RunAsync();
    return 0;
}

using var cts = new CancellationTokenSource();
Console.CancelKeyPress += (_, e) =>
{
    e.Cancel = true;
    cts.Cancel();
};
AppDomain.CurrentDomain.ProcessExit += (_, _) => cts.Cancel();
await Worker.RunAsync(ds, cts.Token);
return 0;

static Dictionary<string, string> Validate(string name, string email, ref string status)
{
    var errors = new Dictionary<string, string>();
    if (string.IsNullOrEmpty(name)) errors["name"] = "Name is required";
    if (string.IsNullOrEmpty(email)) errors["email"] = "Email is required";
    if (!Models.Statuses.Contains(status)) status = "new";
    return errors;
}
