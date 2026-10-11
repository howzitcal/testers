package com.example.leads.scheduler;

import com.example.leads.model.AuditLog;
import com.example.leads.repository.AuditLogRepository;
import com.example.leads.repository.LeadRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class HealthCheckScheduler {

    private static final Logger log = LoggerFactory.getLogger(HealthCheckScheduler.class);

    private final AuditLogRepository auditLogRepository;
    private final LeadRepository leadRepository;

    public HealthCheckScheduler(AuditLogRepository auditLogRepository, LeadRepository leadRepository) {
        this.auditLogRepository = auditLogRepository;
        this.leadRepository = leadRepository;
    }

    @Scheduled(fixedRate = 1800000)
    public void healthCheck() {
        long leadCount = leadRepository.count();
        String message = "System health check OK — lead count=" + leadCount;
        auditLogRepository.save(new AuditLog(message));
        log.info(message);
    }
}
