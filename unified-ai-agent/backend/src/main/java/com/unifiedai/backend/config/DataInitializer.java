package com.unifiedai.backend.config;

import com.unifiedai.backend.entity.UserEntity;
import com.unifiedai.backend.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public DataInitializer(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        seedUserIfNotExists("demo-user", "demo-user@janseva.gov.in", "password123", "demo-user");
        seedUserIfNotExists("rural-farmer", "rural-farmer@janseva.gov.in", "password123", "rural-farmer");
        seedUserIfNotExists("senior-citizen", "senior-citizen@janseva.gov.in", "password123", "senior-citizen");
    }

    private void seedUserIfNotExists(String username, String email, String rawPassword, String citizenId) {
        if (!userRepository.existsByUsername(username)) {
            String encodedPassword = passwordEncoder.encode(rawPassword);
            UserEntity user = new UserEntity(citizenId, username, email, encodedPassword, "CITIZEN");
            userRepository.save(user);
            log.info("Initialized default user account for citizen: {}", citizenId);
        }
    }
}
