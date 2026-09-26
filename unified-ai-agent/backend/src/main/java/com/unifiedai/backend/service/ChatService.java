package com.unifiedai.backend.service;

import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.dto.ChatRequestDto;
import com.unifiedai.backend.dto.ChatResponseDto;
import com.unifiedai.backend.dto.NeedsDetectRequestDto;
import com.unifiedai.backend.dto.NeedsDetectResponseDto;
import com.unifiedai.backend.entity.readonly.CitizenNeedProjection;
import com.unifiedai.backend.repository.CitizenNeedRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ChatService {

    private final PythonAiServiceClient aiServiceClient;
    private final CitizenNeedRepository citizenNeedRepository;

    public ChatService(PythonAiServiceClient aiServiceClient, CitizenNeedRepository citizenNeedRepository) {
        this.aiServiceClient = aiServiceClient;
        this.citizenNeedRepository = citizenNeedRepository;
    }

    public ChatResponseDto chat(String citizenId, ChatRequestDto request, String correlationId) {
        return aiServiceClient.chat(citizenId, request, correlationId);
    }

    public NeedsDetectResponseDto detectNeeds(String citizenId, NeedsDetectRequestDto request, String correlationId) {
        return aiServiceClient.detectNeeds(citizenId, request, correlationId);
    }

    public List<CitizenNeedProjection> getCitizenNeeds(String citizenId) {
        return citizenNeedRepository.findAllByCitizenIdOrderByCreatedAtDesc(citizenId);
    }
}
