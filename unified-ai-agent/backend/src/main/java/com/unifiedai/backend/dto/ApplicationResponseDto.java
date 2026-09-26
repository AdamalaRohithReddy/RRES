package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class ApplicationResponseDto {

    @JsonProperty("application_id")
    private String applicationId;

    @JsonProperty("citizen_id")
    private String citizenId;

    @JsonProperty("scheme_name")
    private String schemeName;

    private String status;

    @JsonProperty("submitted_date")
    private LocalDate submittedDate;

    @JsonProperty("last_updated")
    private Instant lastUpdated;

    @JsonProperty("incubator_preference")
    private String incubatorPreference;

    @JsonProperty("milestone_stage")
    private String milestoneStage;

    @JsonProperty("pran_status")
    private String pranStatus;

    @JsonProperty("next_step")
    private String nextStep;

    private Map<String, Object> details;

    @JsonProperty("status_history")
    private List<ApplicationStatusHistoryDto> statusHistory = new ArrayList<>();

    public ApplicationResponseDto() {}

    public String getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(String applicationId) {
        this.applicationId = applicationId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public void setCitizenId(String citizenId) {
        this.citizenId = citizenId;
    }

    public String getSchemeName() {
        return schemeName;
    }

    public void setSchemeName(String schemeName) {
        this.schemeName = schemeName;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public LocalDate getSubmittedDate() {
        return submittedDate;
    }

    public void setSubmittedDate(LocalDate submittedDate) {
        this.submittedDate = submittedDate;
    }

    public Instant getLastUpdated() {
        return lastUpdated;
    }

    public void setLastUpdated(Instant lastUpdated) {
        this.lastUpdated = lastUpdated;
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

    public String getNextStep() {
        return nextStep;
    }

    public void setNextStep(String nextStep) {
        this.nextStep = nextStep;
    }

    public Map<String, Object> getDetails() {
        return details;
    }

    public void setDetails(Map<String, Object> details) {
        this.details = details;
    }

    public List<ApplicationStatusHistoryDto> getStatusHistory() {
        return statusHistory;
    }

    public void setStatusHistory(List<ApplicationStatusHistoryDto> statusHistory) {
        this.statusHistory = statusHistory;
    }
}
