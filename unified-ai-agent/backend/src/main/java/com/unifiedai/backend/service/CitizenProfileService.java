package com.unifiedai.backend.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.unifiedai.backend.dto.UserProfileDto;
import com.unifiedai.backend.entity.CitizenEntity;
import com.unifiedai.backend.entity.CitizenProfileEntity;
import com.unifiedai.backend.repository.CitizenProfileRepository;
import com.unifiedai.backend.repository.CitizenRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.Period;
import java.util.Map;

@Service
public class CitizenProfileService {

    private final CitizenRepository citizenRepository;
    private final CitizenProfileRepository citizenProfileRepository;
    private final ObjectMapper objectMapper;

    public CitizenProfileService(CitizenRepository citizenRepository,
                                 CitizenProfileRepository citizenProfileRepository,
                                 ObjectMapper objectMapper) {
        this.citizenRepository = citizenRepository;
        this.citizenProfileRepository = citizenProfileRepository;
        this.objectMapper = objectMapper;
    }

    public UserProfileDto getProfile(String citizenId) {
        CitizenEntity citizen = citizenRepository.findByCitizenId(citizenId)
                .orElseThrow(() -> new IllegalArgumentException("Citizen not found: " + citizenId));

        CitizenProfileEntity profile = citizenProfileRepository.findByCitizenId(citizenId)
                .orElseGet(() -> {
                    CitizenProfileEntity newProfile = new CitizenProfileEntity(citizenId);
                    return citizenProfileRepository.save(newProfile);
                });

        return mapToDto(citizen, profile);
    }

    @Transactional
    public UserProfileDto updateProfile(String citizenId, UserProfileDto dto) {
        CitizenEntity citizen = citizenRepository.findByCitizenId(citizenId)
                .orElseThrow(() -> new IllegalArgumentException("Citizen not found: " + citizenId));

        CitizenProfileEntity profile = citizenProfileRepository.findByCitizenId(citizenId)
                .orElseGet(() -> new CitizenProfileEntity(citizenId));

        // Update citizen core fields if provided
        if (dto.getName() != null && !dto.getName().isBlank()) {
            citizen.setName(dto.getName());
        }
        if (dto.getDateOfBirth() != null) {
            citizen.setDateOfBirth(dto.getDateOfBirth());
        }
        if (dto.getGender() != null) {
            citizen.setGender(dto.getGender());
        }
        if (dto.getPhone() != null) {
            citizen.setPhone(dto.getPhone());
        }
        citizenRepository.save(citizen);

        // Update profile fields
        if (dto.getState() != null) profile.setState(dto.getState());
        if (dto.getDistrict() != null) profile.setDistrict(dto.getDistrict());
        if (dto.getAnnualIncome() != null) profile.setAnnualIncome(dto.getAnnualIncome());
        if (dto.getOccupation() != null) profile.setOccupation(dto.getOccupation());
        if (dto.getCategory() != null) profile.setCategory(dto.getCategory());
        if (dto.getIsTaxpayer() != null) profile.setTaxpayer(dto.getIsTaxpayer());
        if (dto.getHasDpiitRecognition() != null) profile.setHasDpiitRecognition(dto.getHasDpiitRecognition());
        if (dto.getBusinessIncorporatedYears() != null) profile.setBusinessIncorporatedYears(dto.getBusinessIncorporatedYears());
        if (dto.getLandholdingAcres() != null) profile.setLandholdingAcres(dto.getLandholdingAcres());
        if (dto.getIsDifferentlyAbled() != null) profile.setDifferentlyAbled(dto.getIsDifferentlyAbled());
        if (dto.getDisabilityPercentage() != null) profile.setDisabilityPercentage(dto.getDisabilityPercentage());

        if (dto.getAdditionalAttributes() != null) {
            try {
                profile.setAdditionalAttributes(objectMapper.writeValueAsString(dto.getAdditionalAttributes()));
            } catch (JsonProcessingException e) {
                throw new IllegalArgumentException("Invalid additional attributes format", e);
            }
        }

        citizenProfileRepository.save(profile);
        return mapToDto(citizen, profile);
    }

    private UserProfileDto mapToDto(CitizenEntity citizen, CitizenProfileEntity profile) {
        UserProfileDto dto = new UserProfileDto();
        dto.setCitizenId(citizen.getCitizenId());
        dto.setName(citizen.getName());
        dto.setDateOfBirth(citizen.getDateOfBirth());
        if (citizen.getDateOfBirth() != null) {
            dto.setAge(Period.between(citizen.getDateOfBirth(), LocalDate.now()).getYears());
        }
        dto.setGender(citizen.getGender());
        dto.setPhone(citizen.getPhone());

        dto.setState(profile.getState());
        dto.setDistrict(profile.getDistrict());
        dto.setAnnualIncome(profile.getAnnualIncome());
        dto.setOccupation(profile.getOccupation());
        dto.setCategory(profile.getCategory());
        dto.setIsTaxpayer(profile.isTaxpayer());
        dto.setHasDpiitRecognition(profile.isHasDpiitRecognition());
        dto.setBusinessIncorporatedYears(profile.getBusinessIncorporatedYears());
        dto.setLandholdingAcres(profile.getLandholdingAcres());
        dto.setIsDifferentlyAbled(profile.isDifferentlyAbled());
        dto.setDisabilityPercentage(profile.getDisabilityPercentage());

        if (profile.getAdditionalAttributes() != null && !profile.getAdditionalAttributes().isBlank()) {
            try {
                dto.setAdditionalAttributes(objectMapper.readValue(profile.getAdditionalAttributes(), new TypeReference<Map<String, Object>>() {}));
            } catch (JsonProcessingException ignored) {}
        }

        return dto;
    }
}
