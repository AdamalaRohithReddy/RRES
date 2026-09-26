# Milestone 9 Walkthrough: React + Spring Boot Application Integration

Milestone 9 has been implemented and validated following the approved architecture plan and all reviewer requirements.

---

## 1. Executive Summary & Architecture Overview

Milestone 9 establishes the complete, production-ready, three-tier citizen support platform:

```
[ Citizen Browser (React 18 + Vite + Tailwind) ]
               │  Calls /api/** with JWT
               ▼
[ Spring Boot 3.3.4 Application Backend (Java 25) ]
               │  • Authoritative writer for users, citizens, citizen_profiles, applications, documents
               │  • Validates JWT and enforces strict IDOR protection
               │  • Injects trusted headers: X-Internal-API-Key, X-Citizen-ID, X-Correlation-ID
               ▼
[ Python AI & RAG Service (FastAPI + PyTorch) ]
               │  • Authoritative writer for citizen_needs, document_extracted_fields, eligibility_assessments
               │  • ReAct Agent Orchestrator with tool-calling loop
               │  • Deterministic M5 statutory evaluation & M4 Document AI OCR
               │  • Vector RAG with Qdrant and SentenceTransformers
               ▼
[ MySQL 8.0.44 Database (`citizen_ai_db`) ]
```

---

## 2. Key Architecture Invariants & Enforced Rules

1. **Clear Data Ownership & Single Authoritative Writers:**
   - **Spring Boot Layer (`backend/`)**: Sole runtime writer for `users`, `citizens`, `citizen_profiles`, `applications`, `application_status_history`, and `documents` metadata/lifecycle.
   - **Python AI Layer (`ai-service/`)**: Authoritative owner for `citizen_needs`, `document_extracted_fields`, `eligibility_assessments`, and `government_api_audit_logs`.
   - **Read-Only JPA Projections**: Spring Boot maps Python-owned tables using `@org.hibernate.annotations.Immutable` entities (`DocumentExtractedFieldProjection`, `CitizenNeedProjection`, `EligibilityAssessmentProjection`).
   - **Narrowly Scoped Document Updates**: Python's document write access is strictly confined to updating `apparent_type` and `extracted_text` on an existing `document_id`.

2. **Security & IDOR Isolation:**
   - React communicates **strictly** with Spring Boot; React **never** supplies `citizen_id` or `X-Citizen-ID`.
   - Spring Boot extracts the authenticated `citizen_id` directly from the validated JWT token (`SecurityContextHolder`).
   - All document, application, and profile queries enforce equality against the authenticated `citizen_id`.
   - Spring Boot forwards requests to the Python AI service using trusted internal headers:
     - `X-Internal-API-Key`: validated against `ai_service_internal_key`.
     - `X-Citizen-ID`: derived from JWT.
     - `X-Correlation-ID`: propagated across all service hops.

3. **Deterministic Java Target:**
   - Host JDK: **Oracle JDK 25** (`C:\Program Files\Java\jdk-25`) with Apache Maven 3.9.14.
   - Maven compiler configured with `<release>21</release>` for compatibility with Spring Framework 6.1 ASM and Mockito.

4. **Decoupled Health Probes:**
   - `/api/health/live` / `/health/live`: Fast process liveness probe.
   - `/api/health/ready` / `/health/ready`: Dependency readiness probe evaluating MySQL, Qdrant, embeddings, and LLM state (with graceful degraded tool fallback).

---

## 3. Tier-by-Tier Implementation Details

### Tier 1: Python FastAPI Layer (`ai-service/src/api/`)
- **Schemas (`src/api/schemas/`)**: Pydantic v2 schemas for chat, needs, schemes, eligibility, and documents.
- **Routes (`src/api/routes/`)**:
  - `POST /v1/agent/chat`: Orchestrator execution with citizen context.
  - `POST /v1/needs/detect`: Direct multi-need extraction.
  - `GET /v1/schemes/search`: Semantic vector search with citations.
  - `GET /v1/schemes/discover`: Government scheme discovery.
  - `POST /v1/eligibility/evaluate`: Deterministic statutory eligibility assessment.
  - `POST /v1/documents/analyze`: Document OCR & key-value fact extraction.
  - `GET /health/live` & `GET /health/ready`: Liveness and component readiness.
- **Security & Middleware (`src/api/dependencies.py` & `main.py`)**: RFC 7807 error formatting, correlation ID injection, internal API key validation.

### Tier 2: Spring Boot Application Layer (`backend/`)
- **Maven Configuration (`pom.xml`)**: Spring Boot 3.3.4, Java 25, JJWT 0.12.6, MySQL Connector/J, Actuator, Mockito subclass maker.
- **Data Model & Entities**:
  - `UserEntity`, `CitizenEntity`, `CitizenProfileEntity`, `ApplicationEntity`, `ApplicationStatusHistoryEntity`, `DocumentEntity`.
  - Read-only projections: `DocumentExtractedFieldProjection`, `CitizenNeedProjection`, `EligibilityAssessmentProjection`.
- **Client (`PythonAiServiceClient`)**: Spring 6 `RestClient` with timeout handling and header propagation.
- **Security & Auth (`security/`)**: `JwtTokenProvider`, `JwtAuthenticationFilter`, `CitizenUserDetails`, `SecurityConfig`, `CorsConfig`.
- **Controllers & Services**:
  - `AuthController` & `AuthService`: Registration, login, JWT issuance.
  - `CitizenProfileController` & `CitizenProfileService`: Profile management.
  - `ChatController` & `ChatService`: Citizen conversation & needs detection.
  - `DocumentController` & `DocumentService`: Multipart upload, SHA-256 computation, magic bytes verification, AI analysis delegation.
  - `SchemeController` & `SchemeService`: RAG clause search.
  - `EligibilityController` & `EligibilityService`: Statutory eligibility check.
  - `ApplicationController` & `ApplicationService`: Scheme application submission and timeline audit.
  - `HealthController`: Liveness and readiness probes.
  - `DataInitializer`: Auto-seeds demo accounts (`demo-user`, `rural-farmer`, `senior-citizen`) on startup.

### Tier 3: React Frontend Portal (`frontend/`)
- **Tech Stack**: Vite 5.4, React 18.3, TypeScript 5.5, Tailwind CSS 3.4, Lucide Icons.
- **Citizen Portal Features**:
  - **Auth**: One-click demo login (`demo-user`), registration modal, JWT state management.
  - **Header**: Live service readiness badge (`Services Active` / `Tool Fallback Mode` / `Service Offline`), citizen identity badge.
  - **AI Advisor Tab**: Interactive chat window with thinking trace toggle, verified statutory citation chips (`[Scheme, Section, Page]`), and detected need badges.
  - **Document Locker Tab**: Drag & drop PDF/image upload, OCR facts view with confidence levels (`HIGH`, `MED`, `LOW`), and mandatory statutory disclaimer badge.
  - **Scheme Discovery Tab**: Semantic search with domain filter chips, match percentages, and clause excerpts.
  - **Statutory Eligibility Tab**: Deterministic assessment runner, visual decision banners (`ELIGIBLE`, `INELIGIBLE`, `INCONCLUSIVE`), rule breakdown table, and next steps guidance.
  - **My Applications Tab**: Application tracking, status history audit timeline, and new application submission modal.

---

## 4. Verification & Test Results

### 1. Spring Boot Backend Test Suite
```text
[INFO] Running com.unifiedai.backend.ApplicationServiceTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.unifiedai.backend.AuthControllerTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.unifiedai.backend.DocumentServiceTest
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.unifiedai.backend.JwtTokenProviderTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
[INFO] Running com.unifiedai.backend.PythonAiServiceClientTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS (15 tests passed, 0 failures, 0 errors)
[INFO] ------------------------------------------------------------------------
```

### 2. Python AI Service Regression Suite
```text
======================= 242 passed, 2 skipped in 68.18s =======================
```
- Includes 14 new API routes & security tests (`tests/test_api_routes.py`, `tests/test_api_security.py`).
- 100% passing tests across M1–M8 without regressions.

### 3. M1 Statutory Retrieval Benchmark
```text
Total Queries Evaluated: 10
- Hit@1: 100.0%
- Hit@3: 100.0%
- Hit@5: 100.0%
- Mean Reciprocal Rank (MRR): 1.0000
- Unrelated Query Discrimination: 100.0%
```

### 4. React Frontend Production Build
```text
> tsc && vite build
✓ 1574 modules transformed.
dist/index.html                   0.81 kB │ gzip:  0.46 kB
dist/assets/index-trLuE5zZ.css   23.67 kB │ gzip:  4.93 kB
dist/assets/index-Dftp9c0M.js   206.31 kB │ gzip: 59.32 kB
✓ built in 16.48s with 0 errors
```

### 5. Live Spring Boot Boot & Integration Smoke Test
- Started `backend-1.0.0-SNAPSHOT.jar` on port 8080.
- `GET /api/health/live` returned `{"status": "UP"}`.
- Auto-seeded `demo-user` in MySQL `users` table.
- `POST /api/auth/login` successfully returned JWT token and validated citizen identity `demo-user`.
