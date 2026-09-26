package com.unifiedai.backend.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class ToolCallDto {

    private String tool;
    private Object input;

    @JsonProperty("result_snippet")
    private String resultSnippet;

    public ToolCallDto() {}

    public String getTool() {
        return tool;
    }

    public void setTool(String tool) {
        this.tool = tool;
    }

    public Object getInput() {
        return input;
    }

    public void setInput(Object input) {
        this.input = input;
    }

    public String getResultSnippet() {
        return resultSnippet;
    }

    public void setResultSnippet(String resultSnippet) {
        this.resultSnippet = resultSnippet;
    }
}
