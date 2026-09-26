package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.ChatRequestDto;
import com.unifiedai.backend.dto.ChatResponseDto;
import com.unifiedai.backend.dto.NeedsDetectRequestDto;
import com.unifiedai.backend.dto.NeedsDetectResponseDto;
import com.unifiedai.backend.entity.readonly.CitizenNeedProjection;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.ChatService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping
    public ResponseEntity<ChatResponseDto> chat(@AuthenticationPrincipal CitizenUserDetails userDetails,
                                                @Valid @RequestBody ChatRequestDto request,
                                                @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        ChatResponseDto response = chatService.chat(userDetails.getCitizenId(), request, correlationId);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/needs")
    public ResponseEntity<NeedsDetectResponseDto> detectNeeds(@AuthenticationPrincipal CitizenUserDetails userDetails,
                                                              @Valid @RequestBody NeedsDetectRequestDto request,
                                                              @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        NeedsDetectResponseDto response = chatService.detectNeeds(userDetails.getCitizenId(), request, correlationId);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/needs")
    public ResponseEntity<List<CitizenNeedProjection>> getCitizenNeeds(@AuthenticationPrincipal CitizenUserDetails userDetails) {
        List<CitizenNeedProjection> needs = chatService.getCitizenNeeds(userDetails.getCitizenId());
        return ResponseEntity.ok(needs);
    }
}
