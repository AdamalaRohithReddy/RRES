package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class NeedsDetectResponseDto {

    private List<DetectedNeedDto> needs = new ArrayList<>();

    @JsonProperty("suggested_scheme_queries")
    private Map<String, List<String>> suggestedSchemeQueries = new HashMap<>();

    public NeedsDetectResponseDto() {}

    public List<DetectedNeedDto> getNeeds() {
        return needs;
    }

    public void setNeeds(List<DetectedNeedDto> needs) {
        this.needs = needs;
    }

    public Map<String, List<String>> getSuggestedSchemeQueries() {
        return suggestedSchemeQueries;
    }

    public void setSuggestedSchemeQueries(Map<String, List<String>> suggestedSchemeQueries) {
        this.suggestedSchemeQueries = suggestedSchemeQueries;
    }
}
