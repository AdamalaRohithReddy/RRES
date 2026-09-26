package com.unifiedai.backend.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.unifiedai.backend.dto.ApplicationCreateRequestDto;
import com.unifiedai.backend.dto.ApplicationResponseDto;
import com.unifiedai.backend.dto.ApplicationStatusHistoryDto;
import com.unifiedai.backend.entity.ApplicationEntity;
import com.unifiedai.backend.entity.ApplicationStatusHistoryEntity;
import com.unifiedai.backend.repository.ApplicationRepository;
import com.unifiedai.backend.repository.ApplicationStatusHistoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;

@Service
public class ApplicationService {

    private final ApplicationRepository applicationRepository;
    private final ApplicationStatusHistoryRepository statusHistoryRepository;
    private final ObjectMapper objectMapper;

    public ApplicationService(ApplicationRepository applicationRepository,
                              ApplicationStatusHistoryRepository statusHistoryRepository,
                              ObjectMapper objectMapper) {
        this.applicationRepository = applicationRepository;
        this.statusHistoryRepository = statusHistoryRepository;
        this.objectMapper = objectMapper;
    }

    public List<ApplicationResponseDto> getCitizenApplications(String citizenId) {
        List<ApplicationEntity> applications = applicationRepository.findAllByCitizenIdOrderByLastUpdatedDesc(citizenId);
        List<ApplicationResponseDto> dtos = new ArrayList<>();
        for (ApplicationEntity app : applications) {
            dtos.add(mapToDto(app, Collections.emptyList()));
        }
        return dtos;
    }

    public ApplicationResponseDto getApplicationDetails(String applicationId, String citizenId) {
        ApplicationEntity app = applicationRepository.findByApplicationIdAndCitizenId(applicationId, citizenId)
                .orElseThrow(() -> new IllegalArgumentException("Application not found or unauthorized"));

        List<ApplicationStatusHistoryEntity> history = statusHistoryRepository.findAllByApplicationIdOrderByCreatedAtDesc(applicationId);
        return mapToDto(app, history);
    }

    @Transactional
    public ApplicationResponseDto createApplication(String citizenId, ApplicationCreateRequestDto request) {
        String appId = "APP-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

        ApplicationEntity app = new ApplicationEntity(appId, citizenId, request.getSchemeName(), "SUBMITTED");
        app.setIncubatorPreference(request.getIncubatorPreference());
        app.setMilestoneStage(request.getMilestoneStage());
        app.setPranStatus(request.getPranStatus());
        app.setNextStep("Document verification and committee evaluation in progress.");

        if (request.getDetails() != null && !request.getDetails().isEmpty()) {
            try {
                app.setDetails(objectMapper.writeValueAsString(request.getDetails()));
            } catch (JsonProcessingException ignored) {}
        }

        applicationRepository.save(app);

        // Record initial history
        ApplicationStatusHistoryEntity history = new ApplicationStatusHistoryEntity(
                appId, "SUBMITTED", "Application submitted successfully by citizen.", "CITIZEN_PORTAL"
        );
        statusHistoryRepository.save(history);

        return mapToDto(app, List.of(history));
    }

    private ApplicationResponseDto mapToDto(ApplicationEntity app, List<ApplicationStatusHistoryEntity> historyList) {
        ApplicationResponseDto dto = new ApplicationResponseDto();
        dto.setApplicationId(app.getApplicationId());
        dto.setCitizenId(app.getCitizenId());
        dto.setSchemeName(app.getSchemeName());
        dto.setStatus(app.getStatus());
        dto.setSubmittedDate(app.getSubmittedDate());
        dto.setLastUpdated(app.getLastUpdated());
        dto.setIncubatorPreference(app.getIncubatorPreference());
        dto.setMilestoneStage(app.getMilestoneStage());
        dto.setPranStatus(app.getPranStatus());
        dto.setNextStep(app.getNextStep());

        if (app.getDetails() != null && !app.getDetails().isBlank()) {
            try {
                dto.setDetails(objectMapper.readValue(app.getDetails(), new TypeReference<Map<String, Object>>() {}));
            } catch (JsonProcessingException ignored) {}
        }

        List<ApplicationStatusHistoryDto> historyDtos = new ArrayList<>();
        for (ApplicationStatusHistoryEntity h : historyList) {
            historyDtos.add(new ApplicationStatusHistoryDto(
                    h.getHistoryId(),
                    h.getStatus(),
                    h.getComment(),
                    h.getChangedBy(),
                    h.getCreatedAt()
            ));
        }
        dto.setStatusHistory(historyDtos);
        return dto;
    }
}
