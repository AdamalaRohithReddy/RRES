package com.unifiedai.backend.entity.readonly;

import jakarta.persistence.*;
import org.hibernate.annotations.Immutable;
import java.time.Instant;

/**
 * Read-only projection for eligibility_assessments.
 * Python Deterministic Eligibility Engine (M5) is the authoritative writer for this table.
 */
@Entity
@Immutable
@Table(name = "eligibility_assessments")
public class EligibilityAssessmentProjection {

    @Id
    @Column(name = "assessment_id")
    private Integer assessmentId;

    @Column(name = "citizen_id", nullable = false, length = 64)
    private String citizenId;

    @Column(name = "scheme_name", nullable = false, length = 255)
    private String schemeName;

    @Column(nullable = false, length = 32)
    private String decision;

    @Column(name = "passed_rules", columnDefinition = "json")
    private String passedRules;

    @Column(name = "failed_rules", columnDefinition = "json")
    private String failedRules;

    @Column(name = "missing_evidence", columnDefinition = "json")
    private String missingEvidence;

    @Column(name = "assessed_at", nullable = false)
    private Instant assessedAt;

    public EligibilityAssessmentProjection() {}

    public Integer getAssessmentId() {
        return assessmentId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public String getSchemeName() {
        return schemeName;
    }

    public String getDecision() {
        return decision;
    }

    public String getPassedRules() {
        return passedRules;
    }

    public String getFailedRules() {
        return failedRules;
    }

    public String getMissingEvidence() {
        return missingEvidence;
    }

    public Instant getAssessedAt() {
        return assessedAt;
    }
}
