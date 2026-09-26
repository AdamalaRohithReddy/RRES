package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.readonly.DocumentExtractedFieldProjection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface DocumentExtractedFieldRepository extends JpaRepository<DocumentExtractedFieldProjection, Integer> {
    List<DocumentExtractedFieldProjection> findAllByDocumentIdOrderByCreatedAtAsc(Integer documentId);
}
