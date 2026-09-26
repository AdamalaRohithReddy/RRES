package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class SchemeSearchResultDto {

    @JsonProperty("scheme_name")
    private String schemeName;

    private String section;

    @JsonProperty("page_number")
    private Integer pageNumber;

    private Double score;
    private String content;

    public SchemeSearchResultDto() {}

    public String getSchemeName() {
        return schemeName;
    }

    public void setSchemeName(String schemeName) {
        this.schemeName = schemeName;
    }

    public String getSection() {
        return section;
    }

    public void setSection(String section) {
        this.section = section;
    }

    public Integer getPageNumber() {
        return pageNumber;
    }

    public void setPageNumber(Integer pageNumber) {
        this.pageNumber = pageNumber;
    }

    public Double getScore() {
        return score;
    }

    public void setScore(Double score) {
        this.score = score;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }
}
