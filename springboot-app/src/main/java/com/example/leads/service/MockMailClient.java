package com.example.leads.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

/**
 * Mock mail client — no SMTP, no network. Logs only.
 */
@Component
public class MockMailClient {

    private static final Logger log = LoggerFactory.getLogger(MockMailClient.class);

    public void send(String toName, String toEmail, String subject, String body) {
        log.info("[MOCK MAIL] to={} <{}> subject=\"{}\" body=\"{}\"", toName, toEmail, subject, body);
    }
}
