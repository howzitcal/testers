package com.example.leads.config;

import jakarta.annotation.PostConstruct;
import java.nio.file.Files;
import java.nio.file.Path;
import org.springframework.stereotype.Component;

@Component
public class DataDirInitializer {

    @PostConstruct
    public void ensureDataDir() throws Exception {
        Files.createDirectories(Path.of("data"));
    }
}
