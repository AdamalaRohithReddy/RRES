package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public class EligibilityEvaluateRequestDto {

    @NotBlank(message = "Scheme name must not be blank")
    @JsonProperty("scheme_name")
    private String schemeName;

    @JsonProperty("citizen_profile")
    private Map<String, Object> citizenProfile;

    public EligibilityEvaluateRequestDto() {}

    public EligibilityEvaluateRequestDto(String schemeName, Map<String, Object> citizenProfile) {
        this.schemeName = schemeName;
        this.citizenProfile = citizenProfile;
    }

    public String getSchemeName() {
        return schemeName;
    }

    public void setSchemeName(String schemeName) {
        this.schemeName = schemeName;
    }

    public Map<String, Object> getCitizenProfile() {
        return citizenProfile;
    }

    public void setCitizenProfile(Map<String, Object> citizenProfile) {
        this.citizenProfile = citizenProfile;
    }
}
