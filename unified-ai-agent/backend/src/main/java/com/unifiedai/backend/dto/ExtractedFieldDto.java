package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ExtractedFieldDto {

    private Object value;
    private Double confidence;

    @JsonProperty("provenance_method")
    private String provenanceMethod;

    public ExtractedFieldDto() {}

    public ExtractedFieldDto(Object value, Double confidence, String provenanceMethod) {
        this.value = value;
        this.confidence = confidence;
        this.provenanceMethod = provenanceMethod;
    }

    public Object getValue() {
        return value;
    }

    public void setValue(Object value) {
        this.value = value;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public String getProvenanceMethod() {
        return provenanceMethod;
    }

    public void setProvenanceMethod(String provenanceMethod) {
        this.provenanceMethod = provenanceMethod;
    }
}
