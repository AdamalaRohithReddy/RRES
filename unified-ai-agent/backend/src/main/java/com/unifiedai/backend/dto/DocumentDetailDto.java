package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

public class DocumentDetailDto {

    @JsonProperty("document_id")
    private Integer documentId;

    @JsonProperty("citizen_id")
    private String citizenId;

    private String filename;

    @JsonProperty("apparent_type")
    private String apparentType;

    @JsonProperty("sha256_hash")
    private String sha256Hash;

    @JsonProperty("uploaded_at")
    private Instant uploadedAt;

    @JsonProperty("extracted_text")
    private String extractedText;

    @JsonProperty("extracted_fields")
    private List<DocumentExtractedFieldDto> extractedFields = new ArrayList<>();

    public DocumentDetailDto() {}

    public Integer getDocumentId() {
        return documentId;
    }

    public void setDocumentId(Integer documentId) {
        this.documentId = documentId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public void setCitizenId(String citizenId) {
        this.citizenId = citizenId;
    }

    public String getFilename() {
        return filename;
    }

    public void setFilename(String filename) {
        this.filename = filename;
    }

    public String getApparentType() {
        return apparentType;
    }

    public void setApparentType(String apparentType) {
        this.apparentType = apparentType;
    }

    public String getSha256Hash() {
        return sha256Hash;
    }

    public void setSha256Hash(String sha256Hash) {
        this.sha256Hash = sha256Hash;
    }

    public Instant getUploadedAt() {
        return uploadedAt;
    }

    public void setUploadedAt(Instant uploadedAt) {
        this.uploadedAt = uploadedAt;
    }

    public String getExtractedText() {
        return extractedText;
    }

    public void setExtractedText(String extractedText) {
        this.extractedText = extractedText;
    }

    public List<DocumentExtractedFieldDto> getExtractedFields() {
        return extractedFields;
    }

    public void setExtractedFields(List<DocumentExtractedFieldDto> extractedFields) {
        this.extractedFields = extractedFields;
    }
}
