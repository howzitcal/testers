use crate::models::{Lead, STATUSES};

fn esc(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn layout(title: &str, body: &str, message: &str) -> String {
    let alert = if message.is_empty() {
        String::new()
    } else {
        format!(r#"<div class="alert alert-success">{}</div>"#, esc(message))
    };
    format!(
        r#"<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-danger mb-4">
    <div class="container">
        <a class="navbar-brand" href="/">Rust Leads</a>
        <a class="btn btn-outline-light btn-sm" href="/leads/new">New Lead</a>
    </div>
</nav>
<main class="container">
    {alert}
    {body}
</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"#,
        title = esc(title),
        alert = alert,
        body = body
    )
}

pub fn render_list(leads: &[Lead], message: &str) -> String {
    let rows = if leads.is_empty() {
        r#"<tr><td colspan="5" class="text-muted">No leads yet.</td></tr>"#.to_string()
    } else {
        leads
            .iter()
            .map(|l| {
                format!(
                    r#"<tr>
            <td>{}</td>
            <td>{}</td>
            <td>{}</td>
            <td><span class="badge text-bg-secondary">{}</span></td>
            <td class="text-end">
                <a class="btn btn-sm btn-outline-primary" href="/leads/{}/edit">Edit</a>
                <form class="d-inline" method="post" action="/leads/{}/delete"
                      onsubmit="return confirm('Delete this lead?');">
                    <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                </form>
            </td>
        </tr>"#,
                    l.id,
                    esc(&l.name),
                    esc(&l.email),
                    esc(&l.status),
                    l.id,
                    l.id
                )
            })
            .collect::<Vec<_>>()
            .join("\n")
    };

    let body = format!(
        r#"
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h3 mb-0">Leads</h1>
        <a class="btn btn-danger" href="/leads/new">Add Lead</a>
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
    </div>"#
    );
    layout("Rust Leads", &body, message)
}

pub fn render_form(
    title: &str,
    name: &str,
    email: &str,
    status: &str,
    errors: &[(String, String)],
) -> String {
    let err = |field: &str| {
        errors
            .iter()
            .find(|(k, _)| k == field)
            .map(|(_, v)| format!(r#"<div class="text-danger">{}</div>"#, esc(v)))
            .unwrap_or_default()
    };
    let options = STATUSES
        .iter()
        .map(|s| {
            format!(
                r#"<option value="{s}" {}>{s}</option>"#,
                if *s == status { "selected" } else { "" }
            )
        })
        .collect::<Vec<_>>()
        .join("\n");

    let body = format!(
        r#"
    <h1 class="h3 mb-3">{title}</h1>
    <form method="post" class="col-md-6">
        <div class="mb-3">
            <label class="form-label" for="id_name">Name</label>
            <input class="form-control" type="text" name="name" id="id_name" value="{name}">
            {name_err}
        </div>
        <div class="mb-3">
            <label class="form-label" for="id_email">Email</label>
            <input class="form-control" type="email" name="email" id="id_email" value="{email}">
            {email_err}
        </div>
        <div class="mb-3">
            <label class="form-label" for="id_status">Status</label>
            <select class="form-select" name="status" id="id_status">
                {options}
            </select>
        </div>
        <button type="submit" class="btn btn-danger">Save</button>
        <a class="btn btn-link" href="/">Cancel</a>
    </form>"#,
        title = esc(title),
        name = esc(name),
        email = esc(email),
        name_err = err("name"),
        email_err = err("email"),
        options = options
    );
    layout(&format!("{title} — Rust Leads"), &body, "")
}
