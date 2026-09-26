package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;

public class CitationDto {

    @JsonProperty("scheme_name")
    @JsonAlias({"scheme_name", "scheme"})
    private String schemeName;

    private String section;

    @JsonProperty("page_number")
    @JsonAlias({"page_number", "page"})
    private Integer pageNumber;

    @JsonProperty("relevance_score")
    @JsonAlias({"relevance_score", "score"})
    private Double relevanceScore;

    @JsonProperty("clause_text")
    @JsonAlias({"clause_text", "content", "text"})
    private String clauseText;

    public CitationDto() {}

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

    public Double getRelevanceScore() {
        return relevanceScore;
    }

    public void setRelevanceScore(Double relevanceScore) {
        this.relevanceScore = relevanceScore;
    }

    public String getClauseText() {
        return clauseText;
    }

    public void setClauseText(String clauseText) {
        this.clauseText = clauseText;
    }
}
