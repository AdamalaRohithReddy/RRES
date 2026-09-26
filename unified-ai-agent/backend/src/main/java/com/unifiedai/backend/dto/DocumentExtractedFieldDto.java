package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

public class DocumentExtractedFieldDto {

    @JsonProperty("field_id")
    private Integer fieldId;

    @JsonProperty("field_name")
    private String fieldName;

    @JsonProperty("field_value")
    private String fieldValue;

    private BigDecimal confidence;

    @JsonProperty("provenance_method")
    private String provenanceMethod;

    public DocumentExtractedFieldDto() {}

    public DocumentExtractedFieldDto(Integer fieldId, String fieldName, String fieldValue, BigDecimal confidence, String provenanceMethod) {
        this.fieldId = fieldId;
        this.fieldName = fieldName;
        this.fieldValue = fieldValue;
        this.confidence = confidence;
        this.provenanceMethod = provenanceMethod;
    }

    public Integer getFieldId() {
        return fieldId;
    }

    public void setFieldId(Integer fieldId) {
        this.fieldId = fieldId;
    }

    public String getFieldName() {
        return fieldName;
    }

    public void setFieldName(String fieldName) {
        this.fieldName = fieldName;
    }

    public String getFieldValue() {
        return fieldValue;
    }

    public void setFieldValue(String fieldValue) {
        this.fieldValue = fieldValue;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public void setConfidence(BigDecimal confidence) {
        this.confidence = confidence;
    }

    public String getProvenanceMethod() {
        return provenanceMethod;
    }

    public void setProvenanceMethod(String provenanceMethod) {
        this.provenanceMethod = provenanceMethod;
    }
}
