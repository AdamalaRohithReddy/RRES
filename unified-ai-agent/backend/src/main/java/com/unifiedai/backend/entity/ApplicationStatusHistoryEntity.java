package com.unifiedai.backend.entity;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "application_status_history")
public class ApplicationStatusHistoryEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "history_id")
    private Integer historyId;

    @Column(name = "application_id", nullable = false, length = 64)
    private String applicationId;

    @Column(nullable = false, length = 100)
    private String status;

    @Column(columnDefinition = "TEXT")
    private String comment;

    @Column(name = "changed_by", length = 100)
    private String changedBy;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "application_id", referencedColumnName = "application_id", insertable = false, updatable = false)
    private ApplicationEntity application;

    public ApplicationStatusHistoryEntity() {}

    public ApplicationStatusHistoryEntity(String applicationId, String status, String comment, String changedBy) {
        this.applicationId = applicationId;
        this.status = status;
        this.comment = comment;
        this.changedBy = changedBy;
        this.createdAt = Instant.now();
    }

    public Integer getHistoryId() {
        return historyId;
    }

    public void setHistoryId(Integer historyId) {
        this.historyId = historyId;
    }

    public String getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(String applicationId) {
        this.applicationId = applicationId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getComment() {
        return comment;
    }

    public void setComment(String comment) {
        this.comment = comment;
    }

    public String getChangedBy() {
        return changedBy;
    }

    public void setChangedBy(String changedBy) {
        this.changedBy = changedBy;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public ApplicationEntity getApplication() {
        return application;
    }

    public void setApplication(ApplicationEntity application) {
        this.application = application;
    }
}
