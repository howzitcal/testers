export const STATUSES = ["new", "contacted", "qualified"];
export const JOB_WELCOME_EMAIL = "welcome_email";

export async function listLeads(pool) {
  const [rows] = await pool.query(
    `SELECT id, name, email, status, created_at FROM leads ORDER BY id`,
  );
  return rows;
}

export async function getLead(pool, id) {
  const [rows] = await pool.query(
    `SELECT id, name, email, status, created_at FROM leads WHERE id = ?`,
    [id],
  );
  return rows[0] ?? null;
}

export async function createLead(pool, name, email, status) {
  const [res] = await pool.query(
    `INSERT INTO leads (name, email, status) VALUES (?, ?, ?)`,
    [name, email, status],
  );
  const lead = await getLead(pool, res.insertId);
  if (!lead) throw new Error("failed to load created lead");
  return lead;
}

export async function updateLead(pool, id, name, email, status) {
  await pool.query(
    `UPDATE leads SET name = ?, email = ?, status = ? WHERE id = ?`,
    [name, email, status, id],
  );
}

export async function deleteLead(pool, id) {
  await pool.query(`DELETE FROM leads WHERE id = ?`, [id]);
}

export async function countLeads(pool) {
  const [rows] = await pool.query(`SELECT COUNT(*) AS n FROM leads`);
  return Number(rows[0].n);
}

export async function createAuditLog(pool, message) {
  await pool.query(`INSERT INTO audit_log (message) VALUES (?)`, [message]);
}

export async function enqueueWelcomeEmail(pool, leadId, name, email) {
  const payload = JSON.stringify({ lead_id: leadId, name, email });
  await pool.query(
    `INSERT INTO background_jobs (job_type, payload, status) VALUES (?, ?, 'pending')`,
    [JOB_WELCOME_EMAIL, payload],
  );
}

export async function claimNextJob(pool) {
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    const [rows] = await conn.query(
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
    const job = rows[0];
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

export async function markJobDone(pool, id) {
  await pool.query(
    `UPDATE background_jobs SET status = 'done', finished_at = UTC_TIMESTAMP(6) WHERE id = ?`,
    [id],
  );
}

export async function markJobFailed(pool, id, error) {
  await pool.query(
    `UPDATE background_jobs SET status = 'failed', error = ?, finished_at = UTC_TIMESTAMP(6) WHERE id = ?`,
    [error, id],
  );
}
