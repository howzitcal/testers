import { loadConfig } from "./src/config.js";
import { ensureDatabase, migrate, openPool } from "./src/db.js";
import { createHandler } from "./src/handlers.js";
import { runWorker } from "./src/worker.js";

const cmd = Bun.argv[2];
if (cmd !== "web" && cmd !== "worker") {
  console.error("usage: bun run main.js <web|worker>");
  process.exit(1);
}

const cfg = loadConfig();
await ensureDatabase(cfg);
const pool = openPool(cfg);
await migrate(pool);

if (cmd === "web") {
  const handler = createHandler(pool);
  console.log(`Bun leads web listening on :${cfg.httpPort}`);
  Bun.serve({
    port: cfg.httpPort,
    fetch: handler,
  });
  await new Promise(() => {});
} else {
  await runWorker(pool);
}
