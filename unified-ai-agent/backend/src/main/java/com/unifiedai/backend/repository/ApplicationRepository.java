package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.ApplicationEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface ApplicationRepository extends JpaRepository<ApplicationEntity, String> {
    List<ApplicationEntity> findAllByCitizenIdOrderByLastUpdatedDesc(String citizenId);
    Optional<ApplicationEntity> findByApplicationIdAndCitizenId(String applicationId, String citizenId);
    boolean existsByApplicationId(String applicationId);
}
