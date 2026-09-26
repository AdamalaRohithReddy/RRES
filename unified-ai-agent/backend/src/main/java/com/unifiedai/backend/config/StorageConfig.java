package com.unifiedai.backend.config;

import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

@Configuration
public class StorageConfig {

    private static final Logger log = LoggerFactory.getLogger(StorageConfig.class);

    @Value("${storage.upload-dir:D:/RRES/unified-ai-agent/uploads/documents}")
    private String uploadDir;

    @PostConstruct
    public void init() {
        try {
            Path path = Paths.get(uploadDir);
            if (!Files.exists(path)) {
                Files.createDirectories(path);
                log.info("Initialized document storage directory: {}", path.toAbsolutePath());
            }
        } catch (IOException e) {
            log.error("Could not initialize storage directory: {}", uploadDir, e);
            throw new RuntimeException("Could not initialize storage directory", e);
        }
    }

    public String getUploadDir() {
        return uploadDir;
    }
}
