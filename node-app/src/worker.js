import { sendMockMail } from "./mail.js";
import {
  JOB_WELCOME_EMAIL,
  claimNextJob,
  countLeads,
  createAuditLog,
  markJobDone,
  markJobFailed,
} from "./models.js";

const POLL_MS = 1000;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function runWorker(pool) {
  console.log("Node worker started (MySQL queue + schedules every 1s)");

  let stopping = false;
  const onStop = () => {
    stopping = true;
  };
  process.on("SIGINT", onStop);
  process.on("SIGTERM", onStop);

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
    console.log("Node worker stopped");
  }
}

async function handleJob(job) {
  if (job.job_type !== JOB_WELCOME_EMAIL) {
    throw new Error(`unknown job_type: ${job.job_type}`);
  }
  const payload = JSON.parse(job.payload);
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

async function runHealthCheck(pool) {
  try {
    const n = await countLeads(pool);
    const msg = `System health check OK — lead count=${n}`;
    await createAuditLog(pool, msg);
    console.log(msg);
  } catch (err) {
    console.error("health check:", err);
  }
}

function dummyJob() {
  console.log("dummy job");
}
