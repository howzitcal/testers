import type { Pool } from "./db.ts";
import { sendMockMail } from "./mail.ts";
import {
  JOB_WELCOME_EMAIL,
  claimNextJob,
  countLeads,
  createAuditLog,
  markJobDone,
  markJobFailed,
} from "./models.ts";

const POLL_MS = 1000;

export async function runWorker(pool: Pool): Promise<void> {
  console.log("Deno worker started (MySQL queue + schedules every 1s)");

  let stopping = false;
  const onStop = () => {
    stopping = true;
  };
  Deno.addSignalListener("SIGINT", onStop);
  Deno.addSignalListener("SIGTERM", onStop);

  const schedule = setInterval(() => {
    void runHealthCheck(pool);
    dummyJob();
  }, 1000);

  try {
    while (!stopping) {
      try {
        const job = await claimNextJob(pool);
        if (!job) {
          await sleep(POLL_MS);
          continue;
        }
        try {
          await handleJob(job);
          await markJobDone(pool, job.id);
        } catch (err) {
          console.error(`Job id=${job.id} failed:`, err);
          await markJobFailed(pool, job.id, String(err));
        }
      } catch (err) {
        console.error("claim job:", err);
        await sleep(POLL_MS);
      }
    }
  } finally {
    clearInterval(schedule);
    console.log("Deno worker stopped");
  }
}

async function handleJob(job: { id: number; job_type: string; payload: string }) {
  if (job.job_type !== JOB_WELCOME_EMAIL) {
    throw new Error(`unknown job_type: ${job.job_type}`);
  }
  const payload = JSON.parse(job.payload) as {
    lead_id: number;
    name: string;
    email: string;
  };
  console.log(
    `Processing welcome_email job id=${job.id} lead_id=${payload.lead_id}`,
  );
  await sleep(500);
  sendMockMail(
    payload.name,
    payload.email,
    "Welcome!",
    `Thanks for signing up, ${payload.name}.`,
  );
}

async function runHealthCheck(pool: Pool): Promise<void> {
  try {
    const n = await countLeads(pool);
    const msg = `System health check OK — lead count=${n}`;
    await createAuditLog(pool, msg);
    console.log(msg);
  } catch (err) {
    console.error("health check:", err);
  }
}

function dummyJob(): void {
  console.log("dummy job");
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
