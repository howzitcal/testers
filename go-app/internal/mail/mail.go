package mail

import "log"

// MockMailClient logs only — no SMTP, no network (same as Django).
type MockMailClient struct{}

func (MockMailClient) Send(toName, toEmail, subject, body string) {
	log.Printf("[MOCK MAIL] to=%s <%s> subject=%q body=%q", toName, toEmail, subject, body)
}
