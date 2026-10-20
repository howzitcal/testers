import { loadConfig } from "./src/config.ts";
import { ensureDatabase, migrate, openPool } from "./src/db.ts";
import { createHandler } from "./src/handlers.ts";
import { runWorker } from "./src/worker.ts";

const cmd = Deno.args[0];
if (cmd !== "web" && cmd !== "worker") {
  console.error("usage: deno run -A main.ts <web|worker>");
  Deno.exit(1);
}

const cfg = loadConfig();
await ensureDatabase(cfg);
const pool = openPool(cfg);
await migrate(pool);

if (cmd === "web") {
  const handler = createHandler(pool);
  console.log(`Deno leads web listening on :${cfg.httpPort}`);
  await Deno.serve({ port: cfg.httpPort }, handler).finished;
} else {
  await runWorker(pool);
}
