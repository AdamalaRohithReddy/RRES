package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.EligibilityEvaluateRequestDto;
import com.unifiedai.backend.dto.EligibilityEvaluateResponseDto;
import com.unifiedai.backend.entity.readonly.EligibilityAssessmentProjection;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.EligibilityService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/eligibility")
public class EligibilityController {

    private final EligibilityService eligibilityService;

    public EligibilityController(EligibilityService eligibilityService) {
        this.eligibilityService = eligibilityService;
    }

    @PostMapping("/check")
    public ResponseEntity<EligibilityEvaluateResponseDto> checkEligibility(
            @AuthenticationPrincipal CitizenUserDetails userDetails,
            @Valid @RequestBody EligibilityEvaluateRequestDto request,
            @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        EligibilityEvaluateResponseDto response = eligibilityService.evaluateEligibility(
                userDetails.getCitizenId(), request, correlationId
        );
        return ResponseEntity.ok(response);
    }

    @GetMapping("/history")
    public ResponseEntity<List<EligibilityAssessmentProjection>> getHistory(
            @AuthenticationPrincipal CitizenUserDetails userDetails) {
        List<EligibilityAssessmentProjection> history = eligibilityService.getCitizenAssessments(userDetails.getCitizenId());
        return ResponseEntity.ok(history);
    }
}
