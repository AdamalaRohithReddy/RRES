package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class RuleEvaluationDto {

    @JsonProperty("rule_id")
    private String ruleId;

    private String description;
    private String status;
    private String evidence;

    public RuleEvaluationDto() {}

    public RuleEvaluationDto(String ruleId, String description, String status, String evidence) {
        this.ruleId = ruleId;
        this.description = description;
        this.status = status;
        this.evidence = evidence;
    }

    public String getRuleId() {
        return ruleId;
    }

    public void setRuleId(String ruleId) {
        this.ruleId = ruleId;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getEvidence() {
        return evidence;
    }

    public void setEvidence(String evidence) {
        this.evidence = evidence;
    }
}
