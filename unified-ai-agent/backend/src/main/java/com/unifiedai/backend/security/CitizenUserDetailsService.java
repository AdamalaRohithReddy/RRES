package com.unifiedai.backend.security;

import com.unifiedai.backend.entity.UserEntity;
import com.unifiedai.backend.repository.UserRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class CitizenUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CitizenUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String usernameOrEmail) throws UsernameNotFoundException {
        UserEntity user = userRepository.findByUsername(usernameOrEmail)
                .or(() -> userRepository.findByEmail(usernameOrEmail))
                .orElseThrow(() -> new UsernameNotFoundException("User not found with username or email: " + usernameOrEmail));

        return new CitizenUserDetails(
                user.getId(),
                user.getCitizenId(),
                user.getUsername(),
                user.getEmail(),
                user.getPasswordHash(),
                user.getRole()
        );
    }
}
