package com.unifiedai.backend.entity.readonly;

import jakarta.persistence.*;
import org.hibernate.annotations.Immutable;
import java.time.Instant;

/**
 * Read-only projection for citizen_needs.
 * Python Multi-Need Detection (M6) is the authoritative writer for this table.
 */
@Entity
@Immutable
@Table(name = "citizen_needs")
public class CitizenNeedProjection {

    @Id
    @Column(name = "need_id")
    private Integer needId;

    @Column(name = "citizen_id", nullable = false, length = 64)
    private String citizenId;

    @Column(nullable = false, length = 64)
    private String category;

    @Column(nullable = false, length = 32)
    private String urgency;

    @Column(name = "need_type", nullable = false, length = 32)
    private String needType;

    @Column(columnDefinition = "TEXT")
    private String statement;

    @Column(name = "session_id", length = 64)
    private String sessionId;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public CitizenNeedProjection() {}

    public Integer getNeedId() {
        return needId;
    }

    public String getCitizenId() {
        return citizenId;
    }

    public String getCategory() {
        return category;
    }

    public String getUrgency() {
        return urgency;
    }

    public String getNeedType() {
        return needType;
    }

    public String getStatement() {
        return statement;
    }

    public String getSessionId() {
        return sessionId;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
