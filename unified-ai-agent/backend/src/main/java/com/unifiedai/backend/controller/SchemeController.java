package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.SchemeSearchResponseDto;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.SchemeService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/schemes")
public class SchemeController {

    private final SchemeService schemeService;

    public SchemeController(SchemeService schemeService) {
        this.schemeService = schemeService;
    }

    @GetMapping("/search")
    public ResponseEntity<SchemeSearchResponseDto> searchSchemes(
            @AuthenticationPrincipal CitizenUserDetails userDetails,
            @RequestParam("q") String query,
            @RequestParam(value = "category", required = false) String category,
            @RequestParam(value = "limit", required = false) Integer limit,
            @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        SchemeSearchResponseDto response = schemeService.searchSchemes(
                userDetails.getCitizenId(), query, category, limit, correlationId
        );
        return ResponseEntity.ok(response);
    }

    @GetMapping("/discover")
    public ResponseEntity<SchemeSearchResponseDto> discoverSchemes(
            @AuthenticationPrincipal CitizenUserDetails userDetails,
            @RequestParam("q") String query,
            @RequestParam(value = "state", required = false) String state,
            @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        SchemeSearchResponseDto response = schemeService.discoverSchemes(
                userDetails.getCitizenId(), query, state, correlationId
        );
        return ResponseEntity.ok(response);
    }
}
