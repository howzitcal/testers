package config

import (
	"fmt"
	"os"
)

// Config mirrors Django's DB_* environment variables for the shared MySQL.
type Config struct {
	DBHost     string
	DBPort     string
	DBUsername string
	DBPassword string
	DBName     string
	HTTPAddr   string
}

func Load() Config {
	return Config{
		DBHost:     getenv("DB_HOST", "host.docker.internal"),
		DBPort:     getenv("DB_PORT", "3306"),
		DBUsername: getenv("DB_USERNAME", "root"),
		DBPassword: getenv("DB_PASSWORD", "password"),
		DBName:     getenv("DB_NAME", "go_leads"),
		HTTPAddr:   getenv("HTTP_ADDR", ":8003"),
	}
}

func (c Config) DSN() string {
	return fmt.Sprintf("%s:%s@tcp(%s:%s)/%s?parseTime=true&charset=utf8mb4&loc=UTC",
		c.DBUsername, c.DBPassword, c.DBHost, c.DBPort, c.DBName)
}

func (c Config) ServerDSN() string {
	// Connect without a database so we can CREATE DATABASE IF NOT EXISTS.
	return fmt.Sprintf("%s:%s@tcp(%s:%s)/?parseTime=true&charset=utf8mb4&loc=UTC",
		c.DBUsername, c.DBPassword, c.DBHost, c.DBPort)
}

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}
