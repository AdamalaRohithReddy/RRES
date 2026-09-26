package com.unifiedai.backend.client;

import com.unifiedai.backend.dto.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.Map;
import java.util.UUID;

@Component
public class PythonAiServiceClient {

    private static final Logger log = LoggerFactory.getLogger(PythonAiServiceClient.class);

    private final RestClient restClient;
    private final String internalApiKey;

    public PythonAiServiceClient(RestClient restClient,
                                 @Value("${ai-service.internal-key:internal-secret-key-change-in-prod}") String internalApiKey) {
        this.restClient = restClient;
        this.internalApiKey = internalApiKey;
    }

    private String getOrCreateCorrelationId(String correlationId) {
        return (correlationId != null && !correlationId.isBlank()) ? correlationId : UUID.randomUUID().toString();
    }

    public ChatResponseDto chat(String citizenId, ChatRequestDto request, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding chat request to Python AI service: citizen={}, corr={}", citizenId, corrId);

        return restClient.post()
                .uri("/v1/agent/chat")
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(ChatResponseDto.class);
    }

    public NeedsDetectResponseDto detectNeeds(String citizenId, NeedsDetectRequestDto request, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding detect-needs request to Python AI service: citizen={}, corr={}", citizenId, corrId);

        return restClient.post()
                .uri("/v1/needs/detect")
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(NeedsDetectResponseDto.class);
    }

    public SchemeSearchResponseDto searchSchemes(String citizenId, String query, String category, Integer limit, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding scheme search request: query='{}', category='{}', citizen={}", query, category, citizenId);

        return restClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/v1/schemes/search")
                        .queryParam("q", query)
                        .queryParamIfPresent("category", java.util.Optional.ofNullable(category))
                        .queryParamIfPresent("limit", java.util.Optional.ofNullable(limit))
                        .build())
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .retrieve()
                .body(SchemeSearchResponseDto.class);
    }

    public SchemeSearchResponseDto discoverSchemes(String citizenId, String query, String state, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding scheme discovery request: query='{}', state='{}', citizen={}", query, state, citizenId);

        return restClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/v1/schemes/discover")
                        .queryParam("q", query)
                        .queryParamIfPresent("state", java.util.Optional.ofNullable(state))
                        .build())
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .retrieve()
                .body(SchemeSearchResponseDto.class);
    }

    public EligibilityEvaluateResponseDto evaluateEligibility(String citizenId, EligibilityEvaluateRequestDto request, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding eligibility evaluation request: scheme={}, citizen={}", request.getSchemeName(), citizenId);

        return restClient.post()
                .uri("/v1/eligibility/evaluate")
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(EligibilityEvaluateResponseDto.class);
    }

    public DocumentAnalyzeResponseDto analyzeDocument(String citizenId, DocumentAnalyzeRequestDto request, String correlationId) {
        String corrId = getOrCreateCorrelationId(correlationId);
        log.info("Forwarding document analysis request: file={}, citizen={}", request.getFilePath(), citizenId);

        return restClient.post()
                .uri("/v1/documents/analyze")
                .header("X-Internal-API-Key", internalApiKey)
                .header("X-Citizen-ID", citizenId)
                .header("X-Correlation-ID", corrId)
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(DocumentAnalyzeResponseDto.class);
    }

    public Map<String, Object> checkLiveness() {
        return restClient.get()
                .uri("/health/live")
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }

    public Map<String, Object> checkReadiness() {
        return restClient.get()
                .uri("/health/ready")
                .retrieve()
                .body(new ParameterizedTypeReference<Map<String, Object>>() {});
    }
}
