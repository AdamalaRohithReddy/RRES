package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.HashMap;
import java.util.Map;

public class DocumentAnalyzeResponseDto {

    @JsonProperty("apparent_document_type")
    private String apparentDocumentType;

    private Map<String, ExtractedFieldDto> fields = new HashMap<>();

    @JsonProperty("classification_confidence")
    private Double classificationConfidence;

    private String disclaimer;

    public DocumentAnalyzeResponseDto() {}

    public String getApparentDocumentType() {
        return apparentDocumentType;
    }

    public void setApparentDocumentType(String apparentDocumentType) {
        this.apparentDocumentType = apparentDocumentType;
    }

    public Map<String, ExtractedFieldDto> getFields() {
        return fields;
    }

    public void setFields(Map<String, ExtractedFieldDto> fields) {
        this.fields = fields;
    }

    public Double getClassificationConfidence() {
        return classificationConfidence;
    }

    public void setClassificationConfidence(Double classificationConfidence) {
        this.classificationConfidence = classificationConfidence;
    }

    public String getDisclaimer() {
        return disclaimer;
    }

    public void setDisclaimer(String disclaimer) {
        this.disclaimer = disclaimer;
    }
}
