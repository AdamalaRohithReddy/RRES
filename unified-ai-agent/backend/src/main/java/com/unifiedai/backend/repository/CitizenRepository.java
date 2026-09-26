package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.CitizenEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CitizenRepository extends JpaRepository<CitizenEntity, String> {
    Optional<CitizenEntity> findByCitizenId(String citizenId);
    boolean existsByCitizenId(String citizenId);
}
