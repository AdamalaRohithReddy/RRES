package com.unifiedai.backend.service;

import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.dto.SchemeSearchResponseDto;
import org.springframework.stereotype.Service;

@Service
public class SchemeService {

    private final PythonAiServiceClient aiServiceClient;

    public SchemeService(PythonAiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    public SchemeSearchResponseDto searchSchemes(String citizenId, String query, String category, Integer limit, String correlationId) {
        return aiServiceClient.searchSchemes(citizenId, query, category, limit, correlationId);
    }

    public SchemeSearchResponseDto discoverSchemes(String citizenId, String query, String state, String correlationId) {
        return aiServiceClient.discoverSchemes(citizenId, query, state, correlationId);
    }
}
