package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public class DocumentAnalyzeRequestDto {

    @NotBlank(message = "file_path is required")
    @JsonProperty("file_path")
    private String filePath;

    @JsonProperty("document_id")
    private Integer documentId;

    @JsonProperty("citizen_id")
    private String citizenId;

    public DocumentAnalyzeRequestDto() {}

    public DocumentAnalyzeRequestDto(String filePath, Integer documentId, String citizenId) {
        this.filePath = filePath;
        this.documentId = documentId;
        this.citizenId = citizenId;
    }

    public String getFilePath() {
        return filePath;
    }

    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }

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
}
