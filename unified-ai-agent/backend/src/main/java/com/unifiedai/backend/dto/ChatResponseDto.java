package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

public class ChatResponseDto {

    @JsonProperty("response")
    @JsonAlias({"response", "answer", "text"})
    private String response;

    @JsonProperty("conversation_id")
    @JsonAlias({"conversation_id", "session_id"})
    private String conversationId;

    @JsonProperty("thought_trace_summary")
    private String thoughtTraceSummary;

    @JsonProperty("citations")
    @JsonAlias({"citations", "sources"})
    private List<CitationDto> citations = new ArrayList<>();

    @JsonProperty("detected_needs")
    private List<DetectedNeedDto> detectedNeeds = new ArrayList<>();

    @JsonProperty("tool_calls_executed")
    @JsonAlias({"tool_calls_executed", "tools_called"})
    private List<Object> toolCallsExecuted = new ArrayList<>();

    @JsonProperty("quota_limited")
    private Boolean quotaLimited;

    public ChatResponseDto() {}

    public String getResponse() {
        return response;
    }

    public void setResponse(String response) {
        this.response = response;
    }

    public String getConversationId() {
        return conversationId;
    }

    public void setConversationId(String conversationId) {
        this.conversationId = conversationId;
    }

    public String getThoughtTraceSummary() {
        return thoughtTraceSummary;
    }

    public void setThoughtTraceSummary(String thoughtTraceSummary) {
        this.thoughtTraceSummary = thoughtTraceSummary;
    }

    public List<CitationDto> getCitations() {
        return citations;
    }

    public void setCitations(List<CitationDto> citations) {
        this.citations = citations;
    }

    public List<DetectedNeedDto> getDetectedNeeds() {
        return detectedNeeds;
    }

    public void setDetectedNeeds(List<DetectedNeedDto> detectedNeeds) {
        this.detectedNeeds = detectedNeeds;
    }

    public List<Object> getToolCallsExecuted() {
        return toolCallsExecuted;
    }

    public void setToolCallsExecuted(List<Object> toolCallsExecuted) {
        this.toolCallsExecuted = toolCallsExecuted;
    }

    public Boolean getQuotaLimited() {
        return quotaLimited;
    }

    public void setQuotaLimited(Boolean quotaLimited) {
        this.quotaLimited = quotaLimited;
    }
}
