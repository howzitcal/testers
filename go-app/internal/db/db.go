package db

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/go-sql-driver/mysql"

	"github.com/callum/tester/go-app/internal/config"
)

func EnsureDatabase(cfg config.Config) error {
	var lastErr error
	for attempt := 1; attempt <= 30; attempt++ {
		conn, err := sql.Open("mysql", cfg.ServerDSN())
		if err != nil {
			lastErr = err
			log.Printf("Waiting for MySQL (%d/30): %v", attempt, err)
			time.Sleep(2 * time.Second)
			continue
		}
		if err := conn.Ping(); err != nil {
			_ = conn.Close()
			lastErr = err
			log.Printf("Waiting for MySQL (%d/30): %v", attempt, err)
			time.Sleep(2 * time.Second)
			continue
		}
		q := fmt.Sprintf(
			"CREATE DATABASE IF NOT EXISTS `%s` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci",
			cfg.DBName,
		)
		if _, err := conn.Exec(q); err != nil {
			_ = conn.Close()
			return err
		}
		_ = conn.Close()
		log.Printf("MySQL ready; database `%s` ensured", cfg.DBName)
		return nil
	}
	return fmt.Errorf("could not connect to MySQL: %w", lastErr)
}

func Open(cfg config.Config) (*sql.DB, error) {
	db, err := sql.Open("mysql", cfg.DSN())
	if err != nil {
		return nil, err
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(time.Hour)
	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return db, nil
}

func Migrate(db *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS leads (
			id BIGINT AUTO_INCREMENT PRIMARY KEY,
			name VARCHAR(200) NOT NULL,
			email VARCHAR(200) NOT NULL,
			status VARCHAR(50) NOT NULL DEFAULT 'new',
			created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
		`CREATE TABLE IF NOT EXISTS audit_log (
			id BIGINT AUTO_INCREMENT PRIMARY KEY,
			created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
			message VARCHAR(1000) NOT NULL
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
		`CREATE TABLE IF NOT EXISTS background_jobs (
			id BIGINT AUTO_INCREMENT PRIMARY KEY,
			job_type VARCHAR(100) NOT NULL,
			payload TEXT NOT NULL,
			status VARCHAR(20) NOT NULL DEFAULT 'pending',
			created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
			started_at DATETIME(6) NULL,
			finished_at DATETIME(6) NULL,
			error TEXT NULL
		) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return err
		}
	}
	return nil
}
