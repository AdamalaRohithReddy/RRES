package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public class ChatRequestDto {

    @NotBlank(message = "Query must not be empty")
    @JsonProperty("query")
    @JsonAlias({"message", "text"})
    private String query;

    @JsonProperty("session_id")
    @JsonAlias({"conversation_id", "sessionId"})
    private String sessionId;

    public ChatRequestDto() {}

    public ChatRequestDto(String query) {
        this.query = query;
    }

    public String getQuery() {
        return query;
    }

    public void setQuery(String query) {
        this.query = query;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }
}