package models

import (
	"database/sql"
	"encoding/json"
	"time"
)

var Statuses = []string{"new", "contacted", "qualified"}

type Lead struct {
	ID        int64
	Name      string
	Email     string
	Status    string
	CreatedAt time.Time
}

type AuditLog struct {
	ID        int64
	CreatedAt time.Time
	Message   string
}

type BackgroundJob struct {
	ID         int64
	JobType    string
	Payload    string
	Status     string
	CreatedAt  time.Time
	StartedAt  sql.NullTime
	FinishedAt sql.NullTime
	Error      sql.NullString
}

const JobWelcomeEmail = "welcome_email"

func ListLeads(db *sql.DB) ([]Lead, error) {
	rows, err := db.Query(`SELECT id, name, email, status, created_at FROM leads ORDER BY id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var leads []Lead
	for rows.Next() {
		var l Lead
		if err := rows.Scan(&l.ID, &l.Name, &l.Email, &l.Status, &l.CreatedAt); err != nil {
			return nil, err
		}
		leads = append(leads, l)
	}
	return leads, rows.Err()
}

func GetLead(db *sql.DB, id int64) (*Lead, error) {
	var l Lead
	err := db.QueryRow(
		`SELECT id, name, email, status, created_at FROM leads WHERE id = ?`, id,
	).Scan(&l.ID, &l.Name, &l.Email, &l.Status, &l.CreatedAt)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &l, nil
}

func CreateLead(db *sql.DB, name, email, status string) (*Lead, error) {
	res, err := db.Exec(
		`INSERT INTO leads (name, email, status) VALUES (?, ?, ?)`,
		name, email, status,
	)
	if err != nil {
		return nil, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return nil, err
	}
	return GetLead(db, id)
}

func UpdateLead(db *sql.DB, id int64, name, email, status string) error {
	_, err := db.Exec(
		`UPDATE leads SET name = ?, email = ?, status = ? WHERE id = ?`,
		name, email, status, id,
	)
	return err
}

func DeleteLead(db *sql.DB, id int64) error {
	_, err := db.Exec(`DELETE FROM leads WHERE id = ?`, id)
	return err
}

func CountLeads(db *sql.DB) (int64, error) {
	var n int64
	err := db.QueryRow(`SELECT COUNT(*) FROM leads`).Scan(&n)
	return n, err
}

func CreateAuditLog(db *sql.DB, message string) error {
	_, err := db.Exec(`INSERT INTO audit_log (message) VALUES (?)`, message)
	return err
}

func EnqueueWelcomeEmail(db *sql.DB, leadID int64, name, email string) error {
	payload, err := json.Marshal(map[string]any{
		"lead_id": leadID,
		"name":    name,
		"email":   email,
	})
	if err != nil {
		return err
	}
	_, err = db.Exec(
		`INSERT INTO background_jobs (job_type, payload, status) VALUES (?, ?, 'pending')`,
		JobWelcomeEmail, string(payload),
	)
	return err
}

func ClaimNextJob(db *sql.DB) (*BackgroundJob, error) {
	tx, err := db.Begin()
	if err != nil {
		return nil, err
	}
	defer func() { _ = tx.Rollback() }()

	var j BackgroundJob
	err = tx.QueryRow(`
		SELECT id, job_type, payload, status, created_at, started_at, finished_at, error
		FROM background_jobs
		WHERE status = 'pending'
		ORDER BY id
		LIMIT 1
		FOR UPDATE
	`).Scan(&j.ID, &j.JobType, &j.Payload, &j.Status, &j.CreatedAt, &j.StartedAt, &j.FinishedAt, &j.Error)
	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	now := time.Now().UTC()
	if _, err := tx.Exec(
		`UPDATE background_jobs SET status = 'running', started_at = ? WHERE id = ?`,
		now, j.ID,
	); err != nil {
		return nil, err
	}
	if err := tx.Commit(); err != nil {
		return nil, err
	}
	j.Status = "running"
	j.StartedAt = sql.NullTime{Time: now, Valid: true}
	return &j, nil
}

func MarkJobDone(db *sql.DB, id int64) error {
	_, err := db.Exec(
		`UPDATE background_jobs SET status = 'done', finished_at = ? WHERE id = ?`,
		time.Now().UTC(), id,
	)
	return err
}

func MarkJobFailed(db *sql.DB, id int64, jobErr string) error {
	_, err := db.Exec(
		`UPDATE background_jobs SET status = 'failed', error = ?, finished_at = ? WHERE id = ?`,
		jobErr, time.Now().UTC(), id,
	)
	return err
}
