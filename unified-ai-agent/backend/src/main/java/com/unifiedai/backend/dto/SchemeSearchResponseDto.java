package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

public class SchemeSearchResponseDto {

    private List<SchemeSearchResultDto> results = new ArrayList<>();

    @JsonProperty("total_matches")
    private Integer totalMatches = 0;

    public SchemeSearchResponseDto() {}

    public List<SchemeSearchResultDto> getResults() {
        return results;
    }

    public void setResults(List<SchemeSearchResultDto> results) {
        this.results = results;
    }

    public Integer getTotalMatches() {
        return totalMatches;
    }

    public void setTotalMatches(Integer totalMatches) {
        this.totalMatches = totalMatches;
    }
}
