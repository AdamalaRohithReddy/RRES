package com.unifiedai.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.unifiedai.backend.dto.ApplicationCreateRequestDto;
import com.unifiedai.backend.dto.ApplicationResponseDto;
import com.unifiedai.backend.entity.ApplicationEntity;
import com.unifiedai.backend.entity.ApplicationStatusHistoryEntity;
import com.unifiedai.backend.repository.ApplicationRepository;
import com.unifiedai.backend.repository.ApplicationStatusHistoryRepository;
import com.unifiedai.backend.service.ApplicationService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import java.util.Collections;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

public class ApplicationServiceTest {

    private ApplicationRepository applicationRepository;
    private ApplicationStatusHistoryRepository statusHistoryRepository;
    private ApplicationService applicationService;

    @BeforeEach
    void setUp() {
        applicationRepository = Mockito.mock(ApplicationRepository.class);
        statusHistoryRepository = Mockito.mock(ApplicationStatusHistoryRepository.class);
        applicationService = new ApplicationService(applicationRepository, statusHistoryRepository, new ObjectMapper());
    }

    @Test
    void testCreateApplicationSuccess() {
        ApplicationCreateRequestDto req = new ApplicationCreateRequestDto();
        req.setSchemeName("PM Kisan");
        req.setIncubatorPreference("IIT Madras");

        when(applicationRepository.save(any(ApplicationEntity.class))).thenAnswer(i -> i.getArguments()[0]);
        when(statusHistoryRepository.save(any(ApplicationStatusHistoryEntity.class))).thenAnswer(i -> i.getArguments()[0]);

        ApplicationResponseDto res = applicationService.createApplication("CITIZEN-001", req);

        assertNotNull(res.getApplicationId());
        assertEquals("CITIZEN-001", res.getCitizenId());
        assertEquals("PM Kisan", res.getSchemeName());
        assertEquals("SUBMITTED", res.getStatus());
    }

    @Test
    void testGetApplicationDetailsAuthorized() {
        ApplicationEntity app = new ApplicationEntity("APP-123", "CITIZEN-001", "PM Kisan", "SUBMITTED");
        when(applicationRepository.findByApplicationIdAndCitizenId("APP-123", "CITIZEN-001"))
                .thenReturn(Optional.of(app));
        when(statusHistoryRepository.findAllByApplicationIdOrderByCreatedAtDesc("APP-123"))
                .thenReturn(Collections.emptyList());

        ApplicationResponseDto res = applicationService.getApplicationDetails("APP-123", "CITIZEN-001");
        assertNotNull(res);
        assertEquals("APP-123", res.getApplicationId());
    }

    @Test
    void testGetApplicationDetailsIdorPrevented() {
        // Citizen 002 tries to access Citizen 001's application
        when(applicationRepository.findByApplicationIdAndCitizenId("APP-123", "CITIZEN-002"))
                .thenReturn(Optional.empty());

        assertThrows(IllegalArgumentException.class, () -> {
            applicationService.getApplicationDetails("APP-123", "CITIZEN-002");
        });
    }
}
