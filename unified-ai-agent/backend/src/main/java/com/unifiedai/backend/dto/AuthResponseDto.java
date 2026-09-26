package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AuthResponseDto {

    private String token;

    @JsonProperty("citizen_id")
    private String citizenId;

    private String username;
    private String name;
    private String role;

    public AuthResponseDto() {}

    public AuthResponseDto(String token, String citizenId, String username, String name, String role) {
        this.token = token;
        this.citizenId = citizenId;
        this.username = username;
        this.name = name;
        this.role = role;
    }

    public String getToken() {
        return token;
    }

    public void setToken(String token) {
        this.token = token;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public void setCitizenId(String citizenId) {
        this.citizenId = citizenId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getRole() {
        return role;
    }

    public void setRole(String role) {
        this.role = role;
    }
}
