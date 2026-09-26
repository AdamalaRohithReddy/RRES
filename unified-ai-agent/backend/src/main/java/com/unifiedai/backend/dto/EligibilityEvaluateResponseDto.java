package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

public class EligibilityEvaluateResponseDto {

    @JsonProperty("scheme_name")
    private String schemeName;

    private String decision;
    private String explanation;

    @JsonProperty("confidence_score")
    private Double confidenceScore;

    @JsonProperty("rule_breakdown")
    private List<RuleEvaluationDto> ruleBreakdown = new ArrayList<>();

    @JsonProperty("missing_evidence")
    private List<String> missingEvidence = new ArrayList<>();

    @JsonProperty("next_steps")
    private List<String> nextSteps = new ArrayList<>();

    public EligibilityEvaluateResponseDto() {}

    public String getSchemeName() {
        return schemeName;
    }

    public void setSchemeName(String schemeName) {
        this.schemeName = schemeName;
    }

    public String getDecision() {
        return decision;
    }

    public void setDecision(String decision) {
        this.decision = decision;
    }

    public String getExplanation() {
        return explanation;
    }

    public void setExplanation(String explanation) {
        this.explanation = explanation;
    }

    public Double getConfidenceScore() {
        return confidenceScore;
    }

    public void setConfidenceScore(Double confidenceScore) {
        this.confidenceScore = confidenceScore;
    }

    public List<RuleEvaluationDto> getRuleBreakdown() {
        return ruleBreakdown;
    }

    public void setRuleBreakdown(List<RuleEvaluationDto> ruleBreakdown) {
        this.ruleBreakdown = ruleBreakdown;
    }

    public List<String> getMissingEvidence() {
        return missingEvidence;
    }

    public void setMissingEvidence(List<String> missingEvidence) {
        this.missingEvidence = missingEvidence;
    }

    public List<String> getNextSteps() {
        return nextSteps;
    }

    public void setNextSteps(List<String> nextSteps) {
        this.nextSteps = nextSteps;
    }
}
