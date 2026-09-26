package com.unifiedai.backend;

import com.unifiedai.backend.security.JwtTokenProvider;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class JwtTokenProviderTest {

    private JwtTokenProvider tokenProvider;
    private final String secret = "404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970";
    private final long expirationMs = 3600000; // 1 hour

    @BeforeEach
    void setUp() {
        tokenProvider = new JwtTokenProvider(secret, expirationMs);
    }

    @Test
    void testGenerateAndValidateToken() {
        String token = tokenProvider.generateToken("testuser", "CITIZEN-12345", "CITIZEN");
        assertNotNull(token);
        assertTrue(tokenProvider.validateToken(token));
        assertEquals("testuser", tokenProvider.getUsername(token));
        assertEquals("CITIZEN-12345", tokenProvider.getCitizenId(token));
        assertEquals("CITIZEN", tokenProvider.getRole(token));
    }

    @Test
    void testInvalidTokenRejection() {
        assertFalse(tokenProvider.validateToken("invalid.token.string"));
    }

    @Test
    void testTamperedTokenRejection() {
        String token = tokenProvider.generateToken("testuser", "CITIZEN-12345", "CITIZEN");
        String tampered = token + "xyz";
        assertFalse(tokenProvider.validateToken(tampered));
    }
}
