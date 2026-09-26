package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.readonly.CitizenNeedProjection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CitizenNeedRepository extends JpaRepository<CitizenNeedProjection, Integer> {
    List<CitizenNeedProjection> findAllByCitizenIdOrderByCreatedAtDesc(String citizenId);
}
