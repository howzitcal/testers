import { STATUSES } from "./models.js";

function esc(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function layout(title, body, message = "") {
  const alert = message
    ? `<div class="alert alert-success">${esc(message)}</div>`
    : "";
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${esc(title)}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
<nav class="navbar navbar-expand-lg navbar-dark bg-success mb-4">
    <div class="container">
        <a class="navbar-brand" href="/">Node Leads</a>
        <a class="btn btn-outline-light btn-sm" href="/leads/new">New Lead</a>
    </div>
</nav>
<main class="container">
    ${alert}
    ${body}
</main>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>`;
}

export function renderList(leads, message = "") {
  const rows = leads.length
    ? leads
      .map(
        (l) => `<tr>
            <td>${l.id}</td>
            <td>${esc(l.name)}</td>
            <td>${esc(l.email)}</td>
            <td><span class="badge text-bg-secondary">${esc(l.status)}</span></td>
            <td class="text-end">
                <a class="btn btn-sm btn-outline-primary" href="/leads/${l.id}/edit">Edit</a>
                <form class="d-inline" method="post" action="/leads/${l.id}/delete"
                      onsubmit="return confirm('Delete this lead?');">
                    <button type="submit" class="btn btn-sm btn-outline-danger">Delete</button>
                </form>
            </td>
        </tr>`,
      )
      .join("\n")
    : `<tr><td colspan="5" class="text-muted">No leads yet.</td></tr>`;

  const body = `
    <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="h3 mb-0">Leads</h1>
        <a class="btn btn-success" href="/leads/new">Add Lead</a>
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
            ${rows}
            </tbody>
        </table>
    </div>`;
  return layout("Node Leads", body, message);
}

export function renderForm(opts) {
  const errors = opts.errors ?? {};
  const options = STATUSES.map(
    (s) =>
      `<option value="${s}" ${s === opts.status ? "selected" : ""}>${s}</option>`,
  ).join("\n");

  const body = `
    <h1 class="h3 mb-3">${esc(opts.title)}</h1>
    <form method="post" class="col-md-6">
        <div class="mb-3">
            <label class="form-label" for="id_name">Name</label>
            <input class="form-control" type="text" name="name" id="id_name" value="${esc(opts.name)}">
            ${errors.name ? `<div class="text-danger">${esc(errors.name)}</div>` : ""}
        </div>
        <div class="mb-3">
            <label class="form-label" for="id_email">Email</label>
            <input class="form-control" type="email" name="email" id="id_email" value="${esc(opts.email)}">
            ${errors.email ? `<div class="text-danger">${esc(errors.email)}</div>` : ""}
        </div>
        <div class="mb-3">
            <label class="form-label" for="id_status">Status</label>
            <select class="form-select" name="status" id="id_status">
                ${options}
            </select>
        </div>
        <button type="submit" class="btn btn-success">Save</button>
        <a class="btn btn-link" href="/">Cancel</a>
    </form>`;
  return layout(`${opts.title} — Node Leads`, body);
}
