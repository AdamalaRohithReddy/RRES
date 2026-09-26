package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.UserProfileDto;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.CitizenProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/profile")
public class CitizenProfileController {

    private final CitizenProfileService profileService;

    public CitizenProfileController(CitizenProfileService profileService) {
        this.profileService = profileService;
    }

    @GetMapping
    public ResponseEntity<UserProfileDto> getProfile(@AuthenticationPrincipal CitizenUserDetails userDetails) {
        return ResponseEntity.ok(profileService.getProfile(userDetails.getCitizenId()));
    }

    @PutMapping
    public ResponseEntity<UserProfileDto> updateProfile(@AuthenticationPrincipal CitizenUserDetails userDetails,
                                                        @RequestBody UserProfileDto updateDto) {
        return ResponseEntity.ok(profileService.updateProfile(userDetails.getCitizenId(), updateDto));
    }
}
