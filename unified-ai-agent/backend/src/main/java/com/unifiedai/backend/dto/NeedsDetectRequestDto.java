package com.unifiedai.backend.dto;

import jakarta.validation.constraints.NotBlank;

public class NeedsDetectRequestDto {

    @NotBlank(message = "Text must not be empty")
    private String text;

    public NeedsDetectRequestDto() {}

    public NeedsDetectRequestDto(String text) {
        this.text = text;
    }

    public String getText() {
        return text;
    }

    public void setText(String text) {
        this.text = text;
    }
}
