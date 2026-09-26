package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class DetectedNeedDto {

    private String category;
    private String urgency;

    @JsonProperty("need_type")
    private String needType;

    private String statement;

    public DetectedNeedDto() {}

    public DetectedNeedDto(String category, String urgency, String needType, String statement) {
        this.category = category;
        this.urgency = urgency;
        this.needType = needType;
        this.statement = statement;
    }

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public String getUrgency() {
        return urgency;
    }

    public void setUrgency(String urgency) {
        this.urgency = urgency;
    }

    public String getNeedType() {
        return needType;
    }

    public void setNeedType(String needType) {
        this.needType = needType;
    }

    public String getStatement() {
        return statement;
    }

    public void setStatement(String statement) {
        this.statement = statement;
    }
}
