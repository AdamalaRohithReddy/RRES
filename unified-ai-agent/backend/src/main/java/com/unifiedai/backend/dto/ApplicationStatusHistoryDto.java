package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;

public class ApplicationStatusHistoryDto {

    @JsonProperty("history_id")
    private Integer historyId;

    private String status;
    private String comment;

    @JsonProperty("changed_by")
    private String changedBy;

    @JsonProperty("created_at")
    private Instant createdAt;

    public ApplicationStatusHistoryDto() {}

    public ApplicationStatusHistoryDto(Integer historyId, String status, String comment, String changedBy, Instant createdAt) {
        this.historyId = historyId;
        this.status = status;
        this.comment = comment;
        this.changedBy = changedBy;
        this.createdAt = createdAt;
    }

    public Integer getHistoryId() {
        return historyId;
    }

    public void setHistoryId(Integer historyId) {
        this.historyId = historyId;
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
}
