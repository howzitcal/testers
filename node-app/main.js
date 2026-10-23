import { createServer } from "node:http";
import { loadConfig } from "./src/config.js";
import { ensureDatabase, migrate, openPool } from "./src/db.js";
import { createHandler } from "./src/handlers.js";
import { runWorker } from "./src/worker.js";

const cmd = process.argv[2];
if (cmd !== "web" && cmd !== "worker") {
  console.error("usage: node main.js <web|worker>");
  process.exit(1);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

const cfg = loadConfig();
await ensureDatabase(cfg);
const pool = openPool(cfg);
await migrate(pool);

if (cmd === "web") {
  const handler = createHandler(pool);
  const server = createServer(async (req, res) => {
    try {
      const host = req.headers.host || `localhost:${cfg.httpPort}`;
      const url = new URL(req.url || "/", `http://${host}`);
      const headers = new Headers();
      for (const [k, v] of Object.entries(req.headers)) {
        if (v !== undefined) headers.set(k, Array.isArray(v) ? v.join(", ") : v);
      }
      const method = req.method || "GET";
      const body = ["GET", "HEAD"].includes(method) ? undefined : await readBody(req);
      const request = new Request(url, { method, headers, body });
      const response = await handler(request);
      res.writeHead(response.status, Object.fromEntries(response.headers));
      res.end(Buffer.from(await response.arrayBuffer()));
    } catch (err) {
      console.error(err);
      res.writeHead(500, { "Content-Type": "text/plain" });
      res.end(String(err));
    }
  });
  server.listen(cfg.httpPort, () => {
    console.log(`Node leads web listening on :${cfg.httpPort}`);
  });
} else {
  await runWorker(pool);
}
