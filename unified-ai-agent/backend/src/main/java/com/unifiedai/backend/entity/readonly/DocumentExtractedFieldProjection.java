package com.unifiedai.backend.entity.readonly;

import jakarta.persistence.*;
import org.hibernate.annotations.Immutable;
import java.math.BigDecimal;
import java.time.Instant;

/**
 * Read-only projection for document_extracted_fields.
 * Python Document AI (M4) is the authoritative writer for this table.
 */
@Entity
@Immutable
@Table(name = "document_extracted_fields")
public class DocumentExtractedFieldProjection {

    @Id
    @Column(name = "field_id")
    private Integer fieldId;

    @Column(name = "document_id", nullable = false)
    private Integer documentId;

    @Column(name = "field_name", nullable = false, length = 64)
    private String fieldName;

    @Column(name = "field_value", nullable = false, length = 255)
    private String fieldValue;

    @Column(nullable = false, precision = 4, scale = 3)
    private BigDecimal confidence;

    @Column(name = "provenance_method", length = 64)
    private String provenanceMethod;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    public DocumentExtractedFieldProjection() {}

    public Integer getFieldId() {
        return fieldId;
    }

    public Integer getDocumentId() {
        return documentId;
    }

    public String getFieldName() {
        return fieldName;
    }

    public String getFieldValue() {
        return fieldValue;
    }

    public BigDecimal getConfidence() {
        return confidence;
    }

    public String getProvenanceMethod() {
        return provenanceMethod;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
