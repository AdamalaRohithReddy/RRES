package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.ApplicationStatusHistoryEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ApplicationStatusHistoryRepository extends JpaRepository<ApplicationStatusHistoryEntity, Integer> {
    List<ApplicationStatusHistoryEntity> findAllByApplicationIdOrderByCreatedAtDesc(String applicationId);
}
