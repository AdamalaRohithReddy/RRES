package com.unifiedai.backend.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.Collections;

public class CitizenUserDetails implements UserDetails {

    private final Long userId;
    private final String citizenId;
    private final String username;
    private final String email;
    private final String password;
    private final String role;

    public CitizenUserDetails(Long userId, String citizenId, String username, String email, String password, String role) {
        this.userId = userId;
        this.citizenId = citizenId;
        this.username = username;
        this.email = email;
        this.password = password;
        this.role = (role != null) ? role : "CITIZEN";
    }

    public Long getUserId() {
        return userId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public String getEmail() {
        return email;
    }

    public String getRole() {
        return role;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + role));
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }
}
