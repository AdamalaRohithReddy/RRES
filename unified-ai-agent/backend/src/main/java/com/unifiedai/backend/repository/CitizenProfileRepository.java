package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.CitizenProfileEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CitizenProfileRepository extends JpaRepository<CitizenProfileEntity, Integer> {
    Optional<CitizenProfileEntity> findByCitizenId(String citizenId);
    void deleteByCitizenId(String citizenId);
}
