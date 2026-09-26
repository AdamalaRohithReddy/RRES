package com.unifiedai.backend;

import com.unifiedai.backend.client.PythonAiServiceClient;
import com.unifiedai.backend.config.StorageConfig;
import com.unifiedai.backend.entity.DocumentEntity;
import com.unifiedai.backend.repository.DocumentExtractedFieldRepository;
import com.unifiedai.backend.repository.DocumentRepository;
import com.unifiedai.backend.service.DocumentService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.mock.web.MockMultipartFile;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.when;

public class DocumentServiceTest {

    private DocumentRepository documentRepository;
    private DocumentExtractedFieldRepository extractedFieldRepository;
    private PythonAiServiceClient aiServiceClient;
    private StorageConfig storageConfig;
    private DocumentService documentService;

    @BeforeEach
    void setUp() {
        documentRepository = Mockito.mock(DocumentRepository.class);
        extractedFieldRepository = Mockito.mock(DocumentExtractedFieldRepository.class);
        aiServiceClient = Mockito.mock(PythonAiServiceClient.class);
        storageConfig = Mockito.mock(StorageConfig.class);
        when(storageConfig.getUploadDir()).thenReturn("target/test-uploads");

        documentService = new DocumentService(
                documentRepository,
                extractedFieldRepository,
                aiServiceClient,
                storageConfig
        );
    }

    @Test
    void testDisallowedExtensionRejected() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "script.exe", "application/octet-stream", "dummy binary content".getBytes()
        );

        assertThrows(IllegalArgumentException.class, () -> {
            documentService.uploadAndAnalyze("CITIZEN-001", file, "corr-1");
        });
    }

    @Test
    void testEmptyFileRejected() {
        MockMultipartFile file = new MockMultipartFile(
                "file", "doc.pdf", "application/pdf", new byte[0]
        );

        assertThrows(IllegalArgumentException.class, () -> {
            documentService.uploadAndAnalyze("CITIZEN-001", file, "corr-2");
        });
    }

    @Test
    void testSpoofedExtensionRejectedByMagicBytes() {
        // Filename is .pdf but content is text/plain without %PDF header
        MockMultipartFile file = new MockMultipartFile(
                "file", "fake.pdf", "application/pdf", "This is plain text not pdf".getBytes()
        );

        assertThrows(IllegalArgumentException.class, () -> {
            documentService.uploadAndAnalyze("CITIZEN-001", file, "corr-3");
        });
    }

    @Test
    void testGetDocumentDetailIdorPrevented() {
        // Document 99 belongs to CITIZEN-001; CITIZEN-002 attempts to retrieve it
        when(documentRepository.findByDocumentIdAndCitizenId(99, "CITIZEN-002"))
                .thenReturn(Optional.empty());

        assertThrows(IllegalArgumentException.class, () -> {
            documentService.getDocumentDetail(99, "CITIZEN-002");
        });
    }
}
