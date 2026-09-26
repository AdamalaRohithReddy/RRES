package com.unifiedai.backend.controller;

import com.unifiedai.backend.client.PythonAiServiceClient;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/health")
public class HealthController {

    private final JdbcTemplate jdbcTemplate;
    private final PythonAiServiceClient aiServiceClient;

    public HealthController(JdbcTemplate jdbcTemplate, PythonAiServiceClient aiServiceClient) {
        this.jdbcTemplate = jdbcTemplate;
        this.aiServiceClient = aiServiceClient;
    }

    @GetMapping("/live")
    public ResponseEntity<Map<String, Object>> liveness() {
        return ResponseEntity.ok(Map.of("status", "UP"));
    }

    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> readiness() {
        Map<String, Object> components = new HashMap<>();
        boolean ready = true;

        // 1. MySQL Health Check
        try {
            jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            components.put("mysql", Map.of("status", "UP"));
        } catch (Exception e) {
            components.put("mysql", Map.of("status", "DOWN", "error", e.getMessage()));
            ready = false;
        }

        // 2. Python AI Service Readiness Check
        try {
            Map<String, Object> aiReady = aiServiceClient.checkReadiness();
            components.put("ai_service", (aiReady != null) ? aiReady : Map.of("status", "UP"));
        } catch (Exception e) {
            components.put("ai_service", Map.of("status", "DEGRADED", "error", e.getMessage()));
        }

        Map<String, Object> response = new HashMap<>();
        response.put("status", ready ? "UP" : "DOWN");
        response.put("ready", ready);
        response.put("components", components);

        if (!ready) {
            return ResponseEntity.status(503).body(response);
        }
        return ResponseEntity.ok(response);
    }
}
