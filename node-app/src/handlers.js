import {
  STATUSES,
  createLead,
  deleteLead,
  enqueueWelcomeEmail,
  getLead,
  listLeads,
  updateLead,
} from "./models.js";
import { renderForm, renderList } from "./templates.js";

function html(body, status = 200) {
  return new Response(body, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8" },
  });
}

function redirect(location) {
  return new Response(null, { status: 303, headers: { Location: location } });
}

async function parseForm(req) {
  const text = await req.text();
  return new URLSearchParams(text);
}

function validate(name, email, status) {
  const errors = {};
  if (!name) errors.name = "Name is required";
  if (!email) errors.email = "Email is required";
  const ok = STATUSES.includes(status);
  return { status: ok ? status : "new", errors };
}

export function createHandler(pool) {
  return async (req) => {
    const url = new URL(req.url);
    const { pathname } = url;
    const method = req.method.toUpperCase();

    try {
      if (method === "GET" && pathname === "/") {
        const leads = await listLeads(pool);
        return html(renderList(leads, url.searchParams.get("msg") ?? ""));
      }

      if (method === "GET" && pathname === "/leads/new") {
        return html(
          renderForm({ title: "New Lead", name: "", email: "", status: "new" }),
        );
      }

      if (method === "POST" && pathname === "/leads/new") {
        const form = await parseForm(req);
        const name = (form.get("name") ?? "").trim();
        const email = (form.get("email") ?? "").trim();
        let status = (form.get("status") ?? "new").trim();
        const v = validate(name, email, status);
        status = v.status;
        if (Object.keys(v.errors).length) {
          return html(
            renderForm({
              title: "New Lead",
              name,
              email,
              status,
              errors: v.errors,
            }),
          );
        }
        const lead = await createLead(pool, name, email, status);
        await enqueueWelcomeEmail(pool, lead.id, lead.name, lead.email);
        return redirect(
          "/?msg=" + encodeURIComponent("Lead created; welcome email queued."),
        );
      }

      const editMatch = pathname.match(/^\/leads\/(\d+)\/edit$/);
      if (editMatch) {
        const id = Number(editMatch[1]);
        const lead = await getLead(pool, id);
        if (!lead) return html("Not found", 404);

        if (method === "GET") {
          return html(
            renderForm({
              title: "Edit Lead",
              name: lead.name,
              email: lead.email,
              status: lead.status,
            }),
          );
        }
        if (method === "POST") {
          const form = await parseForm(req);
          const name = (form.get("name") ?? "").trim();
          const email = (form.get("email") ?? "").trim();
          let status = (form.get("status") ?? "new").trim();
          const v = validate(name, email, status);
          status = v.status;
          if (Object.keys(v.errors).length) {
            return html(
              renderForm({
                title: "Edit Lead",
                name,
                email,
                status,
                errors: v.errors,
              }),
            );
          }
          await updateLead(pool, id, name, email, status);
          return redirect("/?msg=" + encodeURIComponent("Lead updated."));
        }
      }

      const deleteMatch = pathname.match(/^\/leads\/(\d+)\/delete$/);
      if (method === "POST" && deleteMatch) {
        await deleteLead(pool, Number(deleteMatch[1]));
        return redirect("/?msg=" + encodeURIComponent("Lead deleted."));
      }

      return html("Not found", 404);
    } catch (err) {
      console.error(err);
      return html(String(err), 500);
    }
  };
}
