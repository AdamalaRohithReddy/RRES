package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.readonly.EligibilityAssessmentProjection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface EligibilityAssessmentRepository extends JpaRepository<EligibilityAssessmentProjection, Integer> {
    List<EligibilityAssessmentProjection> findAllByCitizenIdOrderByAssessedAtDesc(String citizenId);
    List<EligibilityAssessmentProjection> findAllByCitizenIdAndSchemeNameOrderByAssessedAtDesc(String citizenId, String schemeName);
}
