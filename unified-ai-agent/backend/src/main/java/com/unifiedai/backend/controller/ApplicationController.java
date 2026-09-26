package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.ApplicationCreateRequestDto;
import com.unifiedai.backend.dto.ApplicationResponseDto;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.ApplicationService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/applications")
public class ApplicationController {

    private final ApplicationService applicationService;

    public ApplicationController(ApplicationService applicationService) {
        this.applicationService = applicationService;
    }

    @GetMapping
    public ResponseEntity<List<ApplicationResponseDto>> getCitizenApplications(
            @AuthenticationPrincipal CitizenUserDetails userDetails) {
        List<ApplicationResponseDto> applications = applicationService.getCitizenApplications(userDetails.getCitizenId());
        return ResponseEntity.ok(applications);
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApplicationResponseDto> getApplicationDetails(
            @AuthenticationPrincipal CitizenUserDetails userDetails,
            @PathVariable("id") String id) {
        ApplicationResponseDto application = applicationService.getApplicationDetails(id, userDetails.getCitizenId());
        return ResponseEntity.ok(application);
    }

    @PostMapping
    public ResponseEntity<ApplicationResponseDto> createApplication(
            @AuthenticationPrincipal CitizenUserDetails userDetails,
            @Valid @RequestBody ApplicationCreateRequestDto request) {
        ApplicationResponseDto created = applicationService.createApplication(userDetails.getCitizenId(), request);
        return ResponseEntity.ok(created);
    }
}
