package handlers

import (
	"database/sql"
	"html/template"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/callum/tester/go-app/internal/models"
)

type Server struct {
	DB   *sql.DB
	Tmpl *template.Template
}

func New(db *sql.DB, tmpl *template.Template) *Server {
	return &Server{DB: db, Tmpl: tmpl}
}

func (s *Server) Routes() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", s.leadList)
	mux.HandleFunc("GET /leads/new", s.leadCreateForm)
	mux.HandleFunc("POST /leads/new", s.leadCreate)
	mux.HandleFunc("GET /leads/{id}/edit", s.leadEditForm)
	mux.HandleFunc("POST /leads/{id}/edit", s.leadEdit)
	mux.HandleFunc("POST /leads/{id}/delete", s.leadDelete)
	return mux
}

func (s *Server) leadList(w http.ResponseWriter, r *http.Request) {
	leads, err := models.ListLeads(s.DB)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	s.render(w, "list.html", map[string]any{
		"Leads":   leads,
		"Message": r.URL.Query().Get("msg"),
	})
}

func (s *Server) leadCreateForm(w http.ResponseWriter, r *http.Request) {
	s.render(w, "form.html", formData("New Lead", "", "", "new", nil))
}

func (s *Server) leadCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	email := strings.TrimSpace(r.FormValue("email"))
	status := strings.TrimSpace(r.FormValue("status"))
	errors := validate(name, email, &status)
	if len(errors) > 0 {
		s.render(w, "form.html", formData("New Lead", name, email, status, errors))
		return
	}

	lead, err := models.CreateLead(s.DB, name, email, status)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if err := models.EnqueueWelcomeEmail(s.DB, lead.ID, lead.Name, lead.Email); err != nil {
		log.Printf("enqueue welcome email failed: %v", err)
	}
	http.Redirect(w, r, "/?msg=Lead+created%3B+welcome+email+queued.", http.StatusSeeOther)
}

func (s *Server) leadEditForm(w http.ResponseWriter, r *http.Request) {
	id, ok := parseID(r)
	if !ok {
		http.NotFound(w, r)
		return
	}
	lead, err := models.GetLead(s.DB, id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if lead == nil {
		http.NotFound(w, r)
		return
	}
	s.render(w, "form.html", formData("Edit Lead", lead.Name, lead.Email, lead.Status, nil))
}

func (s *Server) leadEdit(w http.ResponseWriter, r *http.Request) {
	id, ok := parseID(r)
	if !ok {
		http.NotFound(w, r)
		return
	}
	lead, err := models.GetLead(s.DB, id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	if lead == nil {
		http.NotFound(w, r)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	email := strings.TrimSpace(r.FormValue("email"))
	status := strings.TrimSpace(r.FormValue("status"))
	errors := validate(name, email, &status)
	if len(errors) > 0 {
		s.render(w, "form.html", formData("Edit Lead", name, email, status, errors))
		return
	}
	if err := models.UpdateLead(s.DB, id, name, email, status); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	http.Redirect(w, r, "/?msg=Lead+updated.", http.StatusSeeOther)
}

func (s *Server) leadDelete(w http.ResponseWriter, r *http.Request) {
	id, ok := parseID(r)
	if !ok {
		http.NotFound(w, r)
		return
	}
	if err := models.DeleteLead(s.DB, id); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	http.Redirect(w, r, "/?msg=Lead+deleted.", http.StatusSeeOther)
}

func (s *Server) render(w http.ResponseWriter, name string, data any) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := s.Tmpl.ExecuteTemplate(w, name, data); err != nil {
		log.Printf("template %s: %v", name, err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func formData(title, name, email, status string, errors map[string]string) map[string]any {
	if errors == nil {
		errors = map[string]string{}
	}
	return map[string]any{
		"Title":    title,
		"Name":     name,
		"Email":    email,
		"Status":   status,
		"Statuses": models.Statuses,
		"Errors":   errors,
	}
}

func parseID(r *http.Request) (int64, bool) {
	id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
	return id, err == nil
}

func validate(name, email string, status *string) map[string]string {
	errors := map[string]string{}
	if name == "" {
		errors["name"] = "Name is required"
	}
	if email == "" {
		errors["email"] = "Email is required"
	}
	ok := false
	for _, s := range models.Statuses {
		if *status == s {
			ok = true
			break
		}
	}
	if !ok {
		*status = "new"
	}
	return errors
}
