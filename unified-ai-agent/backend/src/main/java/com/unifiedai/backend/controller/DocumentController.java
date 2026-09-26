package com.unifiedai.backend.controller;

import com.unifiedai.backend.dto.DocumentDetailDto;
import com.unifiedai.backend.security.CitizenUserDetails;
import com.unifiedai.backend.service.DocumentService;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/api/documents")
public class DocumentController {

    private final DocumentService documentService;

    public DocumentController(DocumentService documentService) {
        this.documentService = documentService;
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DocumentDetailDto> uploadDocument(@AuthenticationPrincipal CitizenUserDetails userDetails,
                                                            @RequestParam("file") MultipartFile file,
                                                            @RequestHeader(value = "X-Correlation-ID", required = false) String correlationId) {
        DocumentDetailDto result = documentService.uploadAndAnalyze(userDetails.getCitizenId(), file, correlationId);
        return ResponseEntity.ok(result);
    }

    @GetMapping
    public ResponseEntity<List<DocumentDetailDto>> getCitizenDocuments(@AuthenticationPrincipal CitizenUserDetails userDetails) {
        List<DocumentDetailDto> documents = documentService.getCitizenDocuments(userDetails.getCitizenId());
        return ResponseEntity.ok(documents);
    }

    @GetMapping("/{id}")
    public ResponseEntity<DocumentDetailDto> getDocumentDetail(@AuthenticationPrincipal CitizenUserDetails userDetails,
                                                               @PathVariable("id") Integer id) {
        DocumentDetailDto document = documentService.getDocumentDetail(id, userDetails.getCitizenId());
        return ResponseEntity.ok(document);
    }
}
