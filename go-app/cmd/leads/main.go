package main

import (
	"log"
	"net/http"
	"os"

	"github.com/callum/tester/go-app/internal/config"
	"github.com/callum/tester/go-app/internal/db"
	"github.com/callum/tester/go-app/internal/handlers"
	"github.com/callum/tester/go-app/internal/web"
	"github.com/callum/tester/go-app/internal/worker"
)

func main() {
	if len(os.Args) < 2 {
		log.Fatalf("usage: %s <web|worker>", os.Args[0])
	}

	cfg := config.Load()
	if err := db.EnsureDatabase(cfg); err != nil {
		log.Fatal(err)
	}
	sqlDB, err := db.Open(cfg)
	if err != nil {
		log.Fatal(err)
	}
	defer sqlDB.Close()
	if err := db.Migrate(sqlDB); err != nil {
		log.Fatal(err)
	}

	switch os.Args[1] {
	case "web":
		tmpl, err := web.ParseTemplates()
		if err != nil {
			log.Fatal(err)
		}
		srv := handlers.New(sqlDB, tmpl)
		log.Printf("Go leads web listening on %s", cfg.HTTPAddr)
		if err := http.ListenAndServe(cfg.HTTPAddr, srv.Routes()); err != nil {
			log.Fatal(err)
		}
	case "worker":
		worker.Run(sqlDB)
	default:
		log.Fatalf("unknown command %q (want web|worker)", os.Args[1])
	}
}
