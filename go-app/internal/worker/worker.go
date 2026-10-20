package worker

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os/signal"
	"syscall"
	"time"

	"github.com/callum/tester/go-app/internal/mail"
	"github.com/callum/tester/go-app/internal/models"
)

const pollInterval = time.Second

// Run drains the MySQL job queue and runs health_check + dummy_job every 1s
// (mirrors Django-Q schedules and Pyramid worker).
func Run(db *sql.DB) {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, syscall.SIGINT)
	defer stop()

	mailer := mail.MockMailClient{}
	sched := time.NewTicker(time.Second)
	defer sched.Stop()

	log.Println("Go worker started (MySQL queue + schedules every 1s)")

	go func() {
		for {
			select {
			case <-ctx.Done():
				return
			case <-sched.C:
				runHealthCheck(db)
				dummyJob()
			}
		}
	}()

	for {
		select {
		case <-ctx.Done():
			log.Println("Go worker stopped")
			return
		default:
			job, err := models.ClaimNextJob(db)
			if err != nil {
				log.Printf("claim job: %v", err)
				sleep(ctx, pollInterval)
				continue
			}
			if job == nil {
				sleep(ctx, pollInterval)
				continue
			}
			if err := handleJob(job, mailer); err != nil {
				log.Printf("Job id=%d failed: %v", job.ID, err)
				_ = models.MarkJobFailed(db, job.ID, err.Error())
				continue
			}
			if err := models.MarkJobDone(db, job.ID); err != nil {
				log.Printf("mark done id=%d: %v", job.ID, err)
			}
		}
	}
}

func sleep(ctx context.Context, d time.Duration) {
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
	case <-t.C:
	}
}

func handleJob(job *models.BackgroundJob, mailer mail.MockMailClient) error {
	switch job.JobType {
	case models.JobWelcomeEmail:
		var payload struct {
			LeadID int64  `json:"lead_id"`
			Name   string `json:"name"`
			Email  string `json:"email"`
		}
		if err := json.Unmarshal([]byte(job.Payload), &payload); err != nil {
			return err
		}
		log.Printf("Processing welcome_email job id=%d lead_id=%d", job.ID, payload.LeadID)
		time.Sleep(500 * time.Millisecond)
		mailer.Send(payload.Name, payload.Email, "Welcome!", "Thanks for signing up, "+payload.Name+".")
		return nil
	default:
		return fmt.Errorf("unknown job_type: %s", job.JobType)
	}
}

func runHealthCheck(db *sql.DB) {
	n, err := models.CountLeads(db)
	if err != nil {
		log.Printf("health check count: %v", err)
		return
	}
	msg := fmt.Sprintf("System health check OK — lead count=%d", n)
	if err := models.CreateAuditLog(db, msg); err != nil {
		log.Printf("health check audit: %v", err)
		return
	}
	log.Println(msg)
}

func dummyJob() {
	log.Println("dummy job")
}
