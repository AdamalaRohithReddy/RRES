package com.unifiedai.backend.entity;

import jakarta.persistence.*;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "applications")
public class ApplicationEntity {

    @Id
    @Column(name = "application_id", nullable = false, length = 64)
    private String applicationId;

    @Column(name = "citizen_id", nullable = false, length = 64)
    private String citizenId;

    @Column(name = "scheme_name", nullable = false, length = 255)
    private String schemeName;

    @Column(nullable = false, length = 100)
    private String status;

    @Column(name = "submitted_date")
    private LocalDate submittedDate;

    @Column(name = "last_updated", nullable = false)
    private Instant lastUpdated = Instant.now();

    @Column(name = "incubator_preference", length = 255)
    private String incubatorPreference;

    @Column(name = "milestone_stage", length = 255)
    private String milestoneStage;

    @Column(name = "pran_status", length = 100)
    private String pranStatus;

    @Column(name = "next_step", columnDefinition = "TEXT")
    private String nextStep;

    @Column(name = "details", columnDefinition = "json")
    private String details;

    @OneToMany(mappedBy = "application", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @OrderBy("createdAt DESC")
    private List<ApplicationStatusHistoryEntity> statusHistory = new ArrayList<>();

    public ApplicationEntity() {}

    public ApplicationEntity(String applicationId, String citizenId, String schemeName, String status) {
        this.applicationId = applicationId;
        this.citizenId = citizenId;
        this.schemeName = schemeName;
        this.status = status;
        this.submittedDate = LocalDate.now();
        this.lastUpdated = Instant.now();
    }

    @PreUpdate
    public void onUpdate() {
        this.lastUpdated = Instant.now();
    }

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

    public String getDetails() {
        return details;
    }

    public void setDetails(String details) {
        this.details = details;
    }

    public List<ApplicationStatusHistoryEntity> getStatusHistory() {
        return statusHistory;
    }

    public void setStatusHistory(List<ApplicationStatusHistoryEntity> statusHistory) {
        this.statusHistory = statusHistory;
    }
}
