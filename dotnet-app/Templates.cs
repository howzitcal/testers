using System.Net;
using System.Text;

namespace DotnetLeads;

public static class Templates
{
    private static string Esc(string s) => WebUtility.HtmlEncode(s);

    private static string Layout(string title, string body, string message = "")
    {
        var alert = string.IsNullOrEmpty(message)
            ? ""
            : $"<div class=\"alert alert-success\">{Esc(message)}</div>";
        return $$"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>{{Esc(title)}}</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head>
            <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-info mb-4">
                <div class="container">
                    <a class="navbar-brand text-dark" href="/">.NET Leads</a>
                    <a class="btn btn-outline-dark btn-sm" href="/leads/new">New Lead</a>
                </div>
            </nav>
            <main class="container">
                {{alert}}
                {{body}}
            </main>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
            </body>
            </html>
            """;
    }

    public static string RenderList(IReadOnlyList<Lead> leads, string message = "")
    {
        var rows = leads.Count == 0
            ? """<tr><td colspan="5" class="text-muted">No leads yet.</td></tr>"""
            : string.Join("\n", leads.Select(l => $"""
                <tr>
                    <td>{l.Id}</td>
                    <td>{Esc(l.Name)}</td>
                    <td>{Esc(l.Email)}</td>
                    <td><span class="badge text-bg-secondary">{Esc(l.Status)}</span></td>
                    <td class="text-end">
                        <a class="btn btn-sm btn-outline-primary" href="/leads/{l.Id}/edit">Edit</a>
                        <form class="d-inline" method="post" action="/leads/{l.Id}/delete"
                              onsubmit="return confirm('Delete this lead?');">
                            <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                        </form>
                    </td>
                </tr>
                """));

        var body = $"""
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h1 class="h3 mb-0">Leads</h1>
                <a class="btn btn-info text-dark" href="/leads/new">Add Lead</a>
            </div>
            <div class="table-responsive">
                <table class="table table-striped align-middle">
                    <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th></th>
                    </tr>
                    </thead>
                    <tbody>
                    {rows}
                    </tbody>
                </table>
            </div>
            """;
        return Layout(".NET Leads", body, message);
    }

    public static string RenderForm(
        string title,
        string name,
        string email,
        string status,
        IReadOnlyDictionary<string, string>? errors = null)
    {
        errors ??= new Dictionary<string, string>();
        var options = new StringBuilder();
        foreach (var s in Models.Statuses)
        {
            var selected = s == status ? "selected" : "";
            options.AppendLine($"<option value=\"{s}\" {selected}>{s}</option>");
        }

        var nameErr = errors.TryGetValue("name", out var ne) ? $"<div class=\"text-danger\">{Esc(ne)}</div>" : "";
        var emailErr = errors.TryGetValue("email", out var ee) ? $"<div class=\"text-danger\">{Esc(ee)}</div>" : "";

        var body = $"""
            <h1 class="h3 mb-3">{Esc(title)}</h1>
            <form method="post" class="col-md-6">
                <div class="mb-3">
                    <label class="form-label" for="id_name">Name</label>
                    <input class="form-control" type="text" name="name" id="id_name" value="{Esc(name)}">
                    {nameErr}
                </div>
                <div class="mb-3">
                    <label class="form-label" for="id_email">Email</label>
                    <input class="form-control" type="email" name="email" id="id_email" value="{Esc(email)}">
                    {emailErr}
                </div>
                <div class="mb-3">
                    <label class="form-label" for="id_status">Status</label>
                    <select class="form-select" name="status" id="id_status">
                        {options}
                    </select>
                </div>
                <button type="submit" class="btn btn-info text-dark">Save</button>
                <a class="btn btn-link" href="/">Cancel</a>
            </form>
            """;
        return Layout($"{title} — .NET Leads", body);
    }
}
