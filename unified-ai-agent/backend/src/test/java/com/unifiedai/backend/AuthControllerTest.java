package com.unifiedai.backend;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.unifiedai.backend.controller.AuthController;
import com.unifiedai.backend.dto.AuthResponseDto;
import com.unifiedai.backend.dto.LoginRequestDto;
import com.unifiedai.backend.dto.RegisterRequestDto;
import com.unifiedai.backend.exception.GlobalExceptionHandler;
import com.unifiedai.backend.service.AuthService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class AuthControllerTest {

    private MockMvc mockMvc;
    private ObjectMapper objectMapper;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        authService = Mockito.mock(AuthService.class);
        AuthController controller = new AuthController(authService);
        mockMvc = MockMvcBuilders.standaloneSetup(controller)
                .setControllerAdvice(new GlobalExceptionHandler())
                .build();

        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
    }

    @Test
    void testRegisterSuccess() throws Exception {
        RegisterRequestDto req = new RegisterRequestDto();
        req.setUsername("newuser");
        req.setEmail("newuser@example.com");
        req.setPassword("secret123");
        req.setName("New Citizen");

        AuthResponseDto resp = new AuthResponseDto("jwt.token.here", "CITIZEN-99", "newuser", "New Citizen", "CITIZEN");
        when(authService.register(any(RegisterRequestDto.class))).thenReturn(resp);

        mockMvc.perform(post("/api/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("jwt.token.here"))
                .andExpect(jsonPath("$.citizen_id").value("CITIZEN-99"))
                .andExpect(jsonPath("$.username").value("newuser"));
    }

    @Test
    void testLoginSuccess() throws Exception {
        LoginRequestDto req = new LoginRequestDto("testuser", "correctpass");
        AuthResponseDto resp = new AuthResponseDto("jwt.token.here", "CITIZEN-01", "testuser", "Test User", "CITIZEN");
        when(authService.login(any(LoginRequestDto.class))).thenReturn(resp);

        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.token").value("jwt.token.here"))
                .andExpect(jsonPath("$.citizen_id").value("CITIZEN-01"));
    }

    @Test
    void testLoginFailure() throws Exception {
        LoginRequestDto req = new LoginRequestDto("testuser", "wrongpass");
        when(authService.login(any(LoginRequestDto.class))).thenThrow(new BadCredentialsException("Invalid username or password"));

        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(req)))
                .andExpect(status().isUnauthorized());
    }
}
