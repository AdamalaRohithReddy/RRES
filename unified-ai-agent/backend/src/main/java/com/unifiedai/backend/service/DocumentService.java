package com.unifiedai.backend.service;

import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.config.StorageConfig;
import com.unifiedai.backend.dto.*;
import com.unifiedai.backend.entity.DocumentEntity;
import com.unifiedai.backend.entity.readonly.DocumentExtractedFieldProjection;
import com.unifiedai.backend.repository.DocumentExtractedFieldRepository;
import com.unifiedai.backend.repository.DocumentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.DigestInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

@Service
public class DocumentService {

    private static final Logger log = LoggerFactory.getLogger(DocumentService.class);

    private static final Set<String> ALLOWED_EXTENSIONS = Set.of("pdf", "png", "jpg", "jpeg");
    private static final Set<String> ALLOWED_MIME_TYPES = Set.of(
            "application/pdf",
            "image/png",
            "image/jpeg"
    );

    private final DocumentRepository documentRepository;
    private final DocumentExtractedFieldRepository extractedFieldRepository;
    private final PythonAiServiceClient aiServiceClient;
    private final StorageConfig storageConfig;

    public DocumentService(DocumentRepository documentRepository,
                           DocumentExtractedFieldRepository extractedFieldRepository,
                           PythonAiServiceClient aiServiceClient,
                           StorageConfig storageConfig) {
        this.documentRepository = documentRepository;
        this.extractedFieldRepository = extractedFieldRepository;
        this.aiServiceClient = aiServiceClient;
        this.storageConfig = storageConfig;
    }

    @Transactional
    public DocumentDetailDto uploadAndAnalyze(String citizenId, MultipartFile file, String correlationId) {
        validateFile(file);

        // 1. Calculate SHA-256 and store file in citizen's designated storage path
        String originalFilename = file.getOriginalFilename();
        String sanitizedFilename = sanitizeFilename(originalFilename);
        String extension = getFileExtension(sanitizedFilename);

        Path citizenDir = Paths.get(storageConfig.getUploadDir(), citizenId);
        try {
            if (!Files.exists(citizenDir)) {
                Files.createDirectories(citizenDir);
            }
        } catch (IOException e) {
            throw new RuntimeException("Could not create citizen storage directory", e);
        }

        String uniqueFileName = UUID.randomUUID().toString() + "_" + sanitizedFilename;
        Path targetPath = citizenDir.resolve(uniqueFileName);

        String sha256Hex;
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (InputStream is = file.getInputStream();
                 DigestInputStream dis = new DigestInputStream(is, digest)) {
                Files.copy(dis, targetPath);
            }
            sha256Hex = bytesToHex(digest.digest());
        } catch (NoSuchAlgorithmException | IOException e) {
            throw new RuntimeException("Failed to process and store document", e);
        }

        // 2. Insert initial document record (Spring-owned)
        DocumentEntity document = new DocumentEntity(
                citizenId,
                sanitizedFilename,
                sha256Hex,
                targetPath.toAbsolutePath().toString().replace("\\", "/")
        );
        document = documentRepository.save(document);

        // 3. Delegate to Python AI service for OCR & fact extraction
        DocumentAnalyzeRequestDto analyzeRequest = new DocumentAnalyzeRequestDto(
                targetPath.toAbsolutePath().toString().replace("\\", "/"),
                document.getDocumentId(),
                citizenId
        );

        try {
            DocumentAnalyzeResponseDto analysisResult = aiServiceClient.analyzeDocument(citizenId, analyzeRequest, correlationId);
            if (analysisResult != null && analysisResult.getApparentDocumentType() != null) {
                document.setApparentType(analysisResult.getApparentDocumentType());
                document = documentRepository.save(document);
            }
        } catch (Exception e) {
            log.warn("Document AI analysis warning for doc {}: {}", document.getDocumentId(), e.getMessage());
        }

        return getDocumentDetail(document.getDocumentId(), citizenId);
    }

    public List<DocumentDetailDto> getCitizenDocuments(String citizenId) {
        List<DocumentEntity> documents = documentRepository.findAllByCitizenIdOrderByUploadedAtDesc(citizenId);
        List<DocumentDetailDto> dtos = new ArrayList<>();
        for (DocumentEntity doc : documents) {
            dtos.add(mapToDto(doc, Collections.emptyList()));
        }
        return dtos;
    }

    public DocumentDetailDto getDocumentDetail(Integer documentId, String citizenId) {
        DocumentEntity doc = documentRepository.findByDocumentIdAndCitizenId(documentId, citizenId)
                .orElseThrow(() -> new IllegalArgumentException("Document not found or unauthorized"));

        List<DocumentExtractedFieldProjection> extractions = extractedFieldRepository.findAllByDocumentIdOrderByCreatedAtAsc(documentId);
        return mapToDto(doc, extractions);
    }

    private void validateFile(MultipartFile file) {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("Cannot upload empty file");
        }
        if (file.getSize() > 10 * 1024 * 1024) {
            throw new IllegalArgumentException("File size exceeds 10MB limit");
        }

        String filename = file.getOriginalFilename();
        if (filename == null || filename.isBlank()) {
            throw new IllegalArgumentException("Filename cannot be blank");
        }

        String extension = getFileExtension(filename).toLowerCase();
        if (!ALLOWED_EXTENSIONS.contains(extension)) {
            throw new IllegalArgumentException("File extension not allowed: " + extension + ". Allowed: PDF, PNG, JPG, JPEG");
        }

        String contentType = file.getContentType();
        if (contentType != null && !ALLOWED_MIME_TYPES.contains(contentType.toLowerCase())) {
            throw new IllegalArgumentException("Content type not allowed: " + contentType);
        }

        // Magic bytes inspection
        try (InputStream is = file.getInputStream()) {
            byte[] header = new byte[8];
            int read = is.read(header);
            if (read < 4) {
                throw new IllegalArgumentException("File is truncated or invalid");
            }
            if (!isValidMagicBytes(header, extension)) {
                throw new IllegalArgumentException("File header does not match declared extension: " + extension);
            }
        } catch (IOException e) {
            throw new IllegalArgumentException("Failed to read file header", e);
        }
    }

    private boolean isValidMagicBytes(byte[] header, String extension) {
        if ("pdf".equals(extension)) {
            // PDF starts with %PDF (0x25, 0x50, 0x44, 0x46)
            return header[0] == 0x25 && header[1] == 0x50 && header[2] == 0x44 && header[3] == 0x46;
        } else if ("png".equals(extension)) {
            // PNG starts with 0x89 0x50 0x4E 0x47
            return (header[0] & 0xFF) == 0x89 && header[1] == 0x50 && header[2] == 0x4E && header[3] == 0x47;
        } else if ("jpg".equals(extension) || "jpeg".equals(extension)) {
            // JPEG starts with 0xFF 0xD8 0xFF
            return (header[0] & 0xFF) == 0xFF && (header[1] & 0xFF) == 0xD8 && (header[2] & 0xFF) == 0xFF;
        }
        return false;
    }

    private String sanitizeFilename(String filename) {
        if (filename == null) return "document";
        String name = Paths.get(filename).getFileName().toString();
        return name.replaceAll("[^a-zA-Z0-9._-]", "_");
    }

    private String getFileExtension(String filename) {
        int idx = filename.lastIndexOf('.');
        return (idx > 0 && idx < filename.length() - 1) ? filename.substring(idx + 1) : "";
    }

    private String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }

    private DocumentDetailDto mapToDto(DocumentEntity doc, List<DocumentExtractedFieldProjection> extractions) {
        DocumentDetailDto dto = new DocumentDetailDto();
        dto.setDocumentId(doc.getDocumentId());
        dto.setCitizenId(doc.getCitizenId());
        dto.setFilename(doc.getFilename());
        dto.setApparentType(doc.getApparentType());
        dto.setSha256Hash(doc.getSha256Hash());
        dto.setUploadedAt(doc.getUploadedAt());
        dto.setExtractedText(doc.getExtractedText());

        List<DocumentExtractedFieldDto> fieldDtos = new ArrayList<>();
        for (DocumentExtractedFieldProjection f : extractions) {
            fieldDtos.add(new DocumentExtractedFieldDto(
                    f.getFieldId(),
                    f.getFieldName(),
                    f.getFieldValue(),
                    f.getConfidence(),
                    f.getProvenanceMethod()
            ));
        }
        dto.setExtractedFields(fieldDtos);
        return dto;
    }
}
