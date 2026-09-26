package com.unifiedai.backend.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.dto.EligibilityEvaluateRequestDto;
import com.unifiedai.backend.dto.EligibilityEvaluateResponseDto;
import com.unifiedai.backend.dto.UserProfileDto;
import com.unifiedai.backend.entity.readonly.EligibilityAssessmentProjection;
import com.unifiedai.backend.repository.EligibilityAssessmentRepository;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class EligibilityService {

    private final PythonAiServiceClient aiServiceClient;
    private final CitizenProfileService profileService;
    private final EligibilityAssessmentRepository assessmentRepository;
    private final ObjectMapper objectMapper;

    public EligibilityService(PythonAiServiceClient aiServiceClient,
                              CitizenProfileService profileService,
                              EligibilityAssessmentRepository assessmentRepository,
                              ObjectMapper objectMapper) {
        this.aiServiceClient = aiServiceClient;
        this.profileService = profileService;
        this.assessmentRepository = assessmentRepository;
        this.objectMapper = objectMapper;
    }

    public EligibilityEvaluateResponseDto evaluateEligibility(String citizenId,
                                                              EligibilityEvaluateRequestDto request,
                                                              String correlationId) {
        // If citizen_profile wasn't provided in the request payload, harvest from MySQL citizen_profiles
        if (request.getCitizenProfile() == null || request.getCitizenProfile().isEmpty()) {
            UserProfileDto profile = profileService.getProfile(citizenId);
            Map<String, Object> profileMap = objectMapper.convertValue(profile, new TypeReference<Map<String, Object>>() {});
            request.setCitizenProfile(profileMap);
        }

        return aiServiceClient.evaluateEligibility(citizenId, request, correlationId);
    }

    public List<EligibilityAssessmentProjection> getCitizenAssessments(String citizenId) {
        return assessmentRepository.findAllByCitizenIdOrderByAssessedAtDesc(citizenId);
    }
}
