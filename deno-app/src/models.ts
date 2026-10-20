import type { Pool } from "./db.ts";
import type {
  ResultSetHeader,
  RowDataPacket,
} from "mysql2/promise";

export const STATUSES = ["new", "contacted", "qualified"] as const;
export const JOB_WELCOME_EMAIL = "welcome_email";

export type Lead = {
  id: number;
  name: string;
  email: string;
  status: string;
  created_at: Date;
};

export type BackgroundJob = {
  id: number;
  job_type: string;
  payload: string;
  status: string;
};

export async function listLeads(pool: Pool): Promise<Lead[]> {
  const [rows] = await pool.query<RowDataPacket[]>(
    `SELECT id, name, email, status, created_at FROM leads ORDER BY id`,
  );
  return rows as Lead[];
}

export async function getLead(pool: Pool, id: number): Promise<Lead | null> {
  const [rows] = await pool.query<RowDataPacket[]>(
    `SELECT id, name, email, status, created_at FROM leads WHERE id = ?`,
    [id],
  );
  return (rows[0] as Lead) ?? null;
}

export async function createLead(
  pool: Pool,
  name: string,
  email: string,
  status: string,
): Promise<Lead> {
  const [res] = await pool.query<ResultSetHeader>(
    `INSERT INTO leads (name, email, status) VALUES (?, ?, ?)`,
    [name, email, status],
  );
  const lead = await getLead(pool, res.insertId);
  if (!lead) throw new Error("failed to load created lead");
  return lead;
}

export async function updateLead(
  pool: Pool,
  id: number,
  name: string,
  email: string,
  status: string,
): Promise<void> {
  await pool.query(
    `UPDATE leads SET name = ?, email = ?, status = ? WHERE id = ?`,
    [name, email, status, id],
  );
}

export async function deleteLead(pool: Pool, id: number): Promise<void> {
  await pool.query(`DELETE FROM leads WHERE id = ?`, [id]);
}

export async function countLeads(pool: Pool): Promise<number> {
  const [rows] = await pool.query<RowDataPacket[]>(
    `SELECT COUNT(*) AS n FROM leads`,
  );
  return Number(rows[0].n);
}

export async function createAuditLog(pool: Pool, message: string): Promise<void> {
  await pool.query(`INSERT INTO audit_log (message) VALUES (?)`, [message]);
}

export async function enqueueWelcomeEmail(
  pool: Pool,
  leadId: number,
  name: string,
  email: string,
): Promise<void> {
  const payload = JSON.stringify({ lead_id: leadId, name, email });
  await pool.query(
    `INSERT INTO background_jobs (job_type, payload, status) VALUES (?, ?, 'pending')`,
    [JOB_WELCOME_EMAIL, payload],
  );
}

export async function claimNextJob(pool: Pool): Promise<BackgroundJob | null> {
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    const [rows] = await conn.query<RowDataPacket[]>(
      `SELECT id, job_type, payload, status
       FROM background_jobs
       WHERE status = 'pending'
       ORDER BY id
       LIMIT 1
       FOR UPDATE`,
    );
    if (!rows.length) {
      await conn.rollback();
      return null;
    }
    const job = rows[0] as BackgroundJob;
    await conn.query(
      `UPDATE background_jobs SET status = 'running', started_at = UTC_TIMESTAMP(6) WHERE id = ?`,
      [job.id],
    );
    await conn.commit();
    return { ...job, status: "running" };
  } catch (err) {
    await conn.rollback();
    throw err;
  } finally {
    conn.release();
  }
}

export async function markJobDone(pool: Pool, id: number): Promise<void> {
  await pool.query(
    `UPDATE background_jobs SET status = 'done', finished_at = UTC_TIMESTAMP(6) WHERE id = ?`,
    [id],
  );
}

export async function markJobFailed(
  pool: Pool,
  id: number,
  error: string,
): Promise<void> {
  await pool.query(
    `UPDATE background_jobs SET status = 'failed', error = ?, finished_at = UTC_TIMESTAMP(6) WHERE id = ?`,
    [error, id],
  );
}
