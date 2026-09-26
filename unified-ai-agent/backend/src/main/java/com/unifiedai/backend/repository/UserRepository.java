package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.UserEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<UserEntity, Long> {
    Optional<UserEntity> findByUsername(String username);
    Optional<UserEntity> findByEmail(String email);
    Optional<UserEntity> findByCitizenId(String citizenId);
    boolean existsByUsername(String username);
    boolean existsByEmail(String email);
    boolean existsByCitizenId(String citizenId);
}
