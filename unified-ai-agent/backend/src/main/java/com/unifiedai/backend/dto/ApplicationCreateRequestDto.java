package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public class ApplicationCreateRequestDto {

    @NotBlank(message = "Scheme name is required")
    @JsonProperty("scheme_name")
    private String schemeName;

    @JsonProperty("incubator_preference")
    private String incubatorPreference;

    @JsonProperty("milestone_stage")
    private String milestoneStage;

    @JsonProperty("pran_status")
    private String pranStatus;

    private Map<String, Object> details;

    public ApplicationCreateRequestDto() {}

    public String getSchemeName() {
        return schemeName;
    }

    public void setSchemeName(String schemeName) {
        this.schemeName = schemeName;
    }

    public String getIncubatorPreference() {
        return incubatorPreference;
    }

    public void setIncubatorPreference(String incubatorPreference) {
        this.incubatorPreference = incubatorPreference;
    }

    public String getMilestoneStage() {
        return milestoneStage;
    }

    public void setMilestoneStage(String milestoneStage) {
        this.milestoneStage = milestoneStage;
    }

    public String getPranStatus() {
        return pranStatus;
    }

    public void setPranStatus(String pranStatus) {
        this.pranStatus = pranStatus;
    }

    public Map<String, Object> getDetails() {
        return details;
    }

    public void setDetails(Map<String, Object> details) {
        this.details = details;
    }
}
