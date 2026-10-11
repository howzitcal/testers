package com.example.leads.service;

import com.example.leads.model.Lead;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

@Service
public class WelcomeEmailService {

    private static final Logger log = LoggerFactory.getLogger(WelcomeEmailService.class);

    private final MockMailClient mailClient;

    public WelcomeEmailService(MockMailClient mailClient) {
        this.mailClient = mailClient;
    }

    @Async
    public void sendWelcomeEmail(Lead lead) {
        log.info("Queueing mocked welcome email for lead id={}", lead.getId());
        try {
            Thread.sleep(500);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        mailClient.send(
                lead.getName(),
                lead.getEmail(),
                "Welcome!",
                "Thanks for signing up, " + lead.getName() + "."
        );
    }
}
