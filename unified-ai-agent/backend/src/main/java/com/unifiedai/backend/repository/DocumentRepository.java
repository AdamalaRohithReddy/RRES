package com.unifiedai.backend.repository;

import com.unifiedai.backend.entity.DocumentEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface DocumentRepository extends JpaRepository<DocumentEntity, Integer> {
    List<DocumentEntity> findAllByCitizenIdOrderByUploadedAtDesc(String citizenId);
    Optional<DocumentEntity> findByDocumentIdAndCitizenId(Integer documentId, String citizenId);
}
