package com.unifiedai.backend.service;

import com.unifiedai.backend.dto.AuthResponseDto;
import com.unifiedai.backend.dto.LoginRequestDto;
import com.unifiedai.backend.dto.RegisterRequestDto;
import com.unifiedai.backend.entity.CitizenEntity;
import com.unifiedai.backend.entity.CitizenProfileEntity;
import com.unifiedai.backend.entity.UserEntity;
import com.unifiedai.backend.repository.CitizenProfileRepository;
import com.unifiedai.backend.repository.CitizenRepository;
import com.unifiedai.backend.repository.UserRepository;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.security.JwtTokenProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final CitizenRepository citizenRepository;
    private final CitizenProfileRepository citizenProfileRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;

    public AuthService(UserRepository userRepository,
                       CitizenRepository citizenRepository,
                       CitizenProfileRepository citizenProfileRepository,
                       PasswordEncoder passwordEncoder,
                       JwtTokenProvider tokenProvider) {
        this.userRepository = userRepository;
        this.citizenRepository = citizenRepository;
        this.citizenProfileRepository = citizenProfileRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenProvider = tokenProvider;
    }

    @Transactional
    public AuthResponseDto register(RegisterRequestDto request) {
        if (userRepository.existsByUsername(request.getUsername())) {
            throw new IllegalArgumentException("Username already exists: " + request.getUsername());
        }
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new IllegalArgumentException("Email already exists: " + request.getEmail());
        }

        String citizenId = request.getCitizenId();
        if (citizenId == null || citizenId.isBlank()) {
            citizenId = "CITIZEN-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();
        } else {
            if (citizenRepository.existsByCitizenId(citizenId)) {
                throw new IllegalArgumentException("Citizen ID already registered: " + citizenId);
            }
        }

        // 1. Create Citizen record
        CitizenEntity citizen = new CitizenEntity(
                citizenId,
                request.getName(),
                request.getDateOfBirth(),
                request.getGender(),
                request.getPhone()
        );
        citizenRepository.save(citizen);

        // 2. Create default CitizenProfile record
        CitizenProfileEntity profile = new CitizenProfileEntity(citizenId);
        citizenProfileRepository.save(profile);

        // 3. Create User record
        String encodedPassword = passwordEncoder.encode(request.getPassword());
        UserEntity user = new UserEntity(
                citizenId,
                request.getUsername(),
                request.getEmail(),
                encodedPassword,
                "CITIZEN"
        );
        userRepository.save(user);

        // 4. Generate JWT
        String token = tokenProvider.generateToken(user.getUsername(), citizenId, user.getRole());
        return new AuthResponseDto(token, citizenId, user.getUsername(), citizen.getName(), user.getRole());
    }

    public AuthResponseDto login(LoginRequestDto request) {
        UserEntity user = userRepository.findByUsername(request.getUsername())
                .or(() -> userRepository.findByEmail(request.getUsername()))
                .orElseThrow(() -> new BadCredentialsException("Invalid username or password"));

        if (!passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
            throw new BadCredentialsException("Invalid username or password");
        }

        CitizenEntity citizen = citizenRepository.findByCitizenId(user.getCitizenId()).orElse(null);
        String citizenName = (citizen != null) ? citizen.getName() : user.getUsername();

        String token = tokenProvider.generateToken(user.getUsername(), user.getCitizenId(), user.getRole());
        return new AuthResponseDto(token, user.getCitizenId(), user.getUsername(), citizenName, user.getRole());
    }

    public AuthResponseDto getCurrentUser(CitizenUserDetails currentUser) {
        CitizenEntity citizen = citizenRepository.findByCitizenId(currentUser.getCitizenId()).orElse(null);
        String name = (citizen != null) ? citizen.getName() : currentUser.getUsername();
        return new AuthResponseDto(null, currentUser.getCitizenId(), currentUser.getUsername(), name, currentUser.getRole());
    }
}
