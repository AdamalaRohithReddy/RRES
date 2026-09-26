package com.unifiedai.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.dto.ChatRequestDto;
import com.unifiedai.backend.dto.ChatResponseDto;
import com.unifiedai.backend.dto.SchemeSearchResponseDto;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

public class PythonAiServiceClientTest {

    private RestClient restClient;
    private MockRestServiceServer mockServer;
    private PythonAiServiceClient client;
    private ObjectMapper objectMapper = new ObjectMapper();
    private final String internalKey = "test-internal-key";

    @BeforeEach
    void setUp() {
        RestClient.Builder builder = RestClient.builder().baseUrl("http://127.0.0.1:8000");
        mockServer = MockRestServiceServer.bindTo(builder).build();
        restClient = builder.build();
        client = new PythonAiServiceClient(restClient, internalKey);
    }

    @Test
    void testChatPropagatesHeaders() throws Exception {
        ChatRequestDto request = new ChatRequestDto("What schemes can help me?");
        ChatResponseDto mockResponse = new ChatResponseDto();
        mockResponse.setResponse("You may qualify for Startup India.");

        mockServer.expect(requestTo("http://127.0.0.1:8000/v1/agent/chat"))
                .andExpect(method(HttpMethod.POST))
                .andExpect(header("X-Internal-API-Key", internalKey))
                .andExpect(header("X-Citizen-ID", "CITIZEN-001"))
                .andExpect(header("X-Correlation-ID", "corr-abc"))
                .andRespond(withSuccess(objectMapper.writeValueAsString(mockResponse), MediaType.APPLICATION_JSON));

        ChatResponseDto response = client.chat("CITIZEN-001", request, "corr-abc");

        assertNotNull(response);
        assertEquals("You may qualify for Startup India.", response.getResponse());
        mockServer.verify();
    }

    @Test
    void testSchemeSearchPropagatesHeaders() throws Exception {
        SchemeSearchResponseDto mockResponse = new SchemeSearchResponseDto();
        mockResponse.setTotalMatches(1);

        mockServer.expect(requestTo("http://127.0.0.1:8000/v1/schemes/search?q=agriculture&category=farmer&limit=5"))
                .andExpect(method(HttpMethod.GET))
                .andExpect(header("X-Internal-API-Key", internalKey))
                .andExpect(header("X-Citizen-ID", "CITIZEN-002"))
                .andRespond(withSuccess(objectMapper.writeValueAsString(mockResponse), MediaType.APPLICATION_JSON));

        SchemeSearchResponseDto response = client.searchSchemes("CITIZEN-002", "agriculture", "farmer", 5, "corr-xyz");

        assertNotNull(response);
        assertEquals(1, response.getTotalMatches());
        mockServer.verify();
    }
}
