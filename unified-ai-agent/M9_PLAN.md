# Milestone 9 Implementation Plan: React + Spring Boot Application Integration (Revised)

## Executive Summary

Milestone 9 transitions the verified, multi-milestone Python AI Service (M1–M8) into a production-grade, citizen-facing web application. This revised plan establishes rigorous boundaries between tiers, establishes single authoritative ownership for all database tables, guarantees identity isolation, and preserves all 228 passing tests and retrieval benchmarks across M1–M8 without alteration.

---

## 1. System Architecture & Service Boundaries

```
[ Citizen ]
    │
    │  HTTPS / REST / JSON
    │  Bearer JWT (Authorization Header)
    │  X-Correlation-ID
    ▼
[ React 18+ Frontend (Vite + TypeScript + Tailwind CSS) ]  -- Port 5173
    │
    │  REST / JSON
    │  Validated Bearer JWT
    │  X-Correlation-ID
    ▼
[ Spring Boot 3 Backend API Gateway (Java 25, Spring Security, Spring Data JPA) ]  -- Port 8080
    │  ├── JwtAuthenticationFilter (Validates JWT -> Resolves authenticated citizen_id)
    │  ├── Application & Identity Management (Authoritative Owner of users, citizens, applications)
    │  ├── Document Storage Manager (Secure filesystem /uploads/documents/{citizenId}/)
    │  └── PythonAiServiceClient (RestClient with X-Internal-API-Key, X-Citizen-ID, X-Correlation-ID)
    │
    │  Internal REST / JSON (Private localhost binding: 127.0.0.1:8000)
    │  Trusted Internal Headers: X-Internal-API-Key, X-Citizen-ID, X-Correlation-ID
    ▼
[ Python AI Service (FastAPI Thin API Layer) ]  -- Port 8000
    ├── Internal Security Dependency (Validates X-Internal-API-Key & binds X-Citizen-ID)
    ├── Primary Agent Route: /v1/agent/chat (Calls AgentOrchestrator)
    ├── Direct Specialized Routes: /v1/needs/detect, /v1/schemes/search, /v1/eligibility/evaluate, /v1/documents/analyze
    │
    │  Existing Unmodified M1–M8 Modules:
    ├── Agent Orchestrator & ToolRegistry (M3)
    ├── Semantic Scheme Search / RAG & Qdrant (M1)
    ├── Document Intelligence & OCR (M4)
    ├── Deterministic Eligibility Engine (M5)
    ├── Multi-Need Detection & Session Tracker (M6)
    └── Government API Integration (M8 myScheme & DigiLocker Adapters)
    │
    ▼
[ MySQL 8.0 Relational Database (`citizen_ai_db`) ]  -- Port 3306
    (Single shared relational database with strict table-level ownership)
```

---

## 2. Deterministic Database Ownership Matrix

To eliminate competing sources of truth, write contention, and cache drift, every table in `citizen_ai_db` is assigned an **authoritative owner**, a **single allowed writer**, and explicit read access rules:

| Table Name | Authoritative Owner | Allowed Writer (Runtime) | Allowed Readers | Access Method | Rationale & Transition Policy |
|---|---|---|---|---|---|
| `users` *(new)* | Spring Boot | Spring Boot | Spring Boot | Spring Data JPA (Read-Write) | Manages authentication credentials, password hashes (BCrypt), and roles. Kept separate from demographic data. |
| `citizens` | Spring Boot | Spring Boot | Spring Boot, Python AI Service | Spring Data JPA (Read-Write) / Python SQLAlchemy (Read-Only in M9 runtime) | Manages citizen registration and demographic identity. Python writes only during M7 test fixtures; at runtime Spring Boot is the sole writer. |
| `citizen_profiles` | Spring Boot | Spring Boot | Spring Boot, Python AI Service | Spring Data JPA (Read-Write) / Python SQLAlchemy (Read-Only in M9 runtime via `CitizenProfileTool`) | Socio-economic attributes edited by citizens. Python reads profile data as factual evidence for eligibility. |
| `applications` | Spring Boot | Spring Boot | Spring Boot, Python AI Service | Spring Data JPA (Read-Write) / Python SQLAlchemy (Read-Only in M9 runtime via `ApplicationStatusTool`) | **Ownership Transition**: Spring Boot becomes the sole authoritative writer of application submissions and state changes. Python M7 `ApplicationRepository` write methods remain strictly for M7 test fixtures; during live M9 operations, Python treats `applications` as read-only. |
| `application_status_history` | Spring Boot | Spring Boot | Spring Boot, Python AI Service | Spring Data JPA (Read-Write) / Python SQLAlchemy (Read-Only in M9 runtime) | Records administrative status transitions. Authoritative audit log maintained by Spring Boot. |
| `documents` | Spring Boot | Spring Boot (sole owner of document lifecycle, metadata, and storage); Python AI Service (narrowly scoped to update AI-processing fields only) | Spring Boot, Python AI Service | Spring Data JPA (Insert/Read/Delete/Update lifecycle) / Python SQLAlchemy (Narrowly scoped update to `apparent_type` & `extracted_text` only) | **Document Boundary**: Spring Boot owns the `documents` table lifecycle, document metadata, and file storage. Python Document AI has no unrestricted write authority; for M4 compatibility, it has narrowly scoped permission to update only the two AI-processing fields (`apparent_type`, `extracted_text`) for an existing document. |
| `document_extracted_fields` | Python AI Service | Python AI Service (`DocumentAI` / M4) | Python AI Service, Spring Boot | Python SQLAlchemy (Read-Write) / Spring Data JPA (**Read-Only Projection**, `@Immutable`) | **AI-Owned Data**: Python owns algorithmic fact extraction and confidence metrics. Spring Boot maps this entity with `@Immutable` to prevent accidental modification. |
| `citizen_needs` | Python AI Service | Python AI Service (`NeedDetector` / M6) | Python AI Service, Spring Boot | Python SQLAlchemy (Read-Write) / Spring Data JPA (**Read-Only Projection**, `@Immutable`) | **AI-Owned Data**: Needs detected from citizen utterances belong strictly to the AI service. Spring Boot reads them as read-only projections for UI cards. |
| `eligibility_assessments` | Python AI Service | Python AI Service (`EligibilityEngine` / M5) | Python AI Service, Spring Boot | Python SQLAlchemy (Read-Write) / Spring Data JPA (**Read-Only Projection**, `@Immutable`) | **AI-Owned Data**: Deterministic statutory assessments and rule breakdowns are produced exclusively by the Python engine. Spring Boot never writes to this table. |
| `government_api_audit_logs` | Python AI Service | Python AI Service (`GovernmentAPIClient` / M8) | Python AI Service, Spring Boot (Audit/Admin) | Python SQLAlchemy (Append-Only) / Spring Data JPA (**Read-Only Projection**, `@Immutable`) | **AI-Owned Data**: Operational audit telemetry for external government API calls. Exclusively written by M8 client. |

---

## 3. Strict Identity Security & Header Flow

### The Zero-Trust Identity Rule
**React is never trusted to supply `citizen_id` or any `X-Citizen-ID` header.**

### End-to-End Flow:
1. **Citizen Authentication**: Citizen authenticates via React using username/email and password (`POST /api/auth/login`).
2. **JWT Issuance**: Spring Boot verifies BCrypt hash, issues a signed HMAC-SHA256 JWT containing claims:
   - `sub`: username/email
   - `citizen_id`: the immutable citizen identifier
   - `role`: user role (`ROLE_CITIZEN`)
   - `iat`, `exp`: issue time and expiry (2 hours)
3. **Frontend Requests**: React stores JWT in memory / secure storage. On all API requests, React sends standard header:
   ```http
   Authorization: Bearer <JWT>
   X-Correlation-ID: <uuid-v4>
   ```
   *React does NOT set `X-Citizen-ID` or include citizen ID in request bodies.*
4. **Spring Boot Validation & Extraction**:
   - `JwtAuthenticationFilter` intercepts the request, validates signature and expiration.
   - Extracts `citizen_id` from the verified token claims.
   - Places `CitizenUserDetails` into Spring's `SecurityContext`.
5. **Spring Boot → Python AI Service Propagation**:
   - When calling the internal Python AI Service, Spring Boot's `PythonAiServiceClient` injects trusted internal headers:
     ```http
     X-Internal-API-Key: ${AI_SERVICE_INTERNAL_KEY}
     X-Citizen-ID: ${authenticated_citizen_id}
     X-Correlation-ID: ${correlation_id}
     ```
6. **Python AI Service Enforcement**:
   - FastAPI dependency `verify_internal_service_credentials` validates `X-Internal-API-Key`. Missing or invalid keys return `401 Unauthorized`.
   - Validates presence of `X-Citizen-ID`. Missing header on citizen-scoped endpoints returns `400 Bad Request`.
   - Binds `X-Citizen-ID` to `CitizenProfileTool` for the duration of the request, eliminating the M7 `demo-user` parameter reliance.

---

## 4. FastAPI Boundary & Thin Adapter Architecture

The FastAPI layer in `src/api/` serves strictly as a **thin transport adapter**. It contains **zero duplicate business logic**:

```
FastAPI Route Handlers (src/api/routes/)
    │
    │  (Unpacks JSON, validates Pydantic request models, passes execution)
    ▼
Existing M1–M8 Service Modules (src/)
    ├── AgentOrchestrator (src/agent/agent.py)
    ├── NeedDetector (src/needs/detector.py)
    ├── SchemeRetriever (src/retrieval/retriever.py)
    ├── EligibilityEngine (src/eligibility/engine.py)
    ├── DocumentAI (src/document_ai/pipeline.py)
    └── GovernmentAPIClient (src/government_api/client.py)
```

### Distinction Between Primary Orchestration and Direct Endpoints

1. **Primary Agent Orchestration Endpoint (`POST /v1/agent/chat`)**:
   - **Purpose**: Main conversational citizen interface.
   - **Behavior**: Executes `AgentOrchestrator.run()`. The LLM reasons over the query and dynamically selects tools from `ToolRegistry` (`search_government_schemes`, `get_citizen_profile`, `detect_citizen_needs`, `check_eligibility`, `analyze_document`, `discover_government_schemes`).
   - **Citizen Context**: Injects the authenticated `X-Citizen-ID` into `CitizenProfileTool`.
2. **Direct Operation Endpoints (Specialized UI Widgets)**:
   - `POST /v1/needs/detect`: Direct call to `NeedDetector.detect_needs()`. Used by the "Needs Assessment" UI tab.
   - `POST /v1/schemes/search`: Direct call to `SchemeRetriever.retrieve()`. Used by the "Scheme Search" search bar.
   - `POST /v1/schemes/discover`: Direct call to `MySchemeAdapter.search_schemes()`. Used by the "Live Directory" browser.
   - `POST /v1/eligibility/evaluate`: Direct call to `EligibilityEngine.evaluate()`. Used by the "Eligibility Check" modal.
   - `POST /v1/documents/analyze`: Direct call to `DocumentAI.analyze()`. Used immediately upon document upload.

---

## 5. Health Endpoints: Liveness vs. Readiness

Liveness and readiness are strictly decoupled. External LLM availability (OpenAI) does not dictate basic service health:

### 1. `/health/live` (Liveness Probe)
- **Path**: `GET /health/live`
- **Purpose**: Verify that the process is alive and accepting connections.
- **Checks**: Zero external dependencies.
- **Response**: `200 OK`
  ```json
  { "status": "UP" }
  ```

### 2. `/health/ready` (Readiness Probe)
- **Path**: `GET /health/ready`
- **Purpose**: Verify that core components required to serve citizen requests are ready.
- **Component Evaluation**:
  - `mysql`: Database connection ping via SQLAlchemy engine. (If down -> `DOWN`, overall `503 Service Unavailable`).
  - `vector_store`: Qdrant client connection / collection verification. (If down -> `DOWN`, overall `503 Service Unavailable`).
  - `embeddings`: SentenceTransformer model loaded in memory. (If not loaded -> `DOWN`, overall `503 Service Unavailable`).
  - `llm`: OpenAI API configuration and credit availability status:
    - **`configured`**: API key is present in environment settings.
    - **`ready`**: API key active and live generation operational.
    - **`degraded`**: API key credit balance exhausted (Error 429) or endpoint unreachable. Overall service status remains **`200 OK (DEGRADED)`** because the agent's verified direct tool fallback is operational!
    - **`disabled`**: No API key provided; direct tool fallback active.
- **Sample Readiness Response (When OpenAI Quota Exhausted)**:
  ```json
  {
    "status": "DEGRADED",
    "ready": true,
    "components": {
      "mysql": { "status": "UP", "database": "citizen_ai_db" },
      "vector_store": { "status": "UP", "collection": "scheme_documents" },
      "embeddings": { "status": "UP", "model": "all-MiniLM-L6-v2" },
      "llm": { "status": "DEGRADED", "state": "configured", "notice": "Quota exhausted (Error 429). Direct tool fallback active." }
    }
  }
  ```

---

## 6. Deterministic Java Version

- **Deterministic Choice**: **Java 25**.
- **Verification**: Verified installed and active on the host machine (`C:\Program Files\Java\jdk-25`) along with Apache Maven 3.9.14.
- **Maven Configuration (`backend/pom.xml`)**:
  ```xml
  <properties>
      <java.version>25</java.version>
      <maven.compiler.source>25</maven.compiler.source>
      <maven.compiler.target>25</maven.compiler.target>
      <spring-boot.version>3.3.4</spring-boot.version>
  </properties>
  ```
  *(Java 25 will be used consistently throughout all backend modules, documentation, and build scripts).*

---

## 7. Document Ownership & Storage Architecture

```
[ Citizen (React) ]
    │  1. Uploads file (PDF/JPEG/PNG <= 10MB)
    ▼
[ Spring Boot: DocumentController ]
    │  2. Validates MIME type & magic bytes (rejects executables/scripts)
    │  3. Saves file to controlled storage:
    │     /uploads/documents/{citizenId}/{uuid}_{sanitizedFilename}
    │  4. Computes SHA-256 hash
    │  5. Inserts initial metadata record into MySQL `documents` table (Spring-owned):
    │     (document_id, citizen_id, filename, sha256_hash, storage_path, uploaded_at)
    ▼
[ Python AI Service: POST /v1/documents/analyze ]
    │  6. Receives `{ "file_path": "/uploads/documents/...", "citizen_id": "..." }`
    │  7. Reads file in-place via PyMuPDF (zero duplicate file copying)
    │  8. Performs Document AI processing (apparent type classification, text extraction, OCR fallback)
    │  9. Extracts key-value facts with confidence scores and provenance methods
    │ 10. Inserts extracted facts into MySQL `document_extracted_fields` (Python-owned)
    │ 11. Narrowly scoped update: sets `apparent_type` and `extracted_text` on existing `documents` record
    ▼
[ Spring Boot: DocumentService ]
    │ 12. Reads extracted fields via read-only projection
    │ 13. Returns structured document response to React
    ▼
[ React Document Card ]
    │ 14. Displays extracted facts + Confidence badges (HIGH/MED/LOW) +
    │     Disclaimer: "Structured facts extracted by Document AI. Does not constitute official government authentication."
```

**Ownership Invariant & Strict Boundary**:
- **Lifecycle & Storage**: Spring Boot is the sole owner of the `documents` table lifecycle (creation, updates to filename/path/metadata, deletion) and controlled filesystem storage.
- **AI-Processing Fields (Narrowly Scoped)**: Python Document AI receives read-only access to the physical document file. For M4 schema compatibility, Python is granted strictly scoped update authority restricted to the two AI-processing columns (`apparent_type` and `extracted_text`) on an existing `document_id`. Python has zero authority to insert, delete, or modify any other metadata or storage fields in `documents`.
- **Extraction Results**: Python owns all extracted facts, confidence metrics, and provenance records in `document_extracted_fields`.
- **Zero Duplicate Storage**: Python reads the file in-place from the secure upload path without creating copies.

---

## 8. Service-to-Service API Specifications

### 1. React → Spring Boot Endpoints (`http://localhost:8080/api`)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Register new citizen user account (`users` + `citizens`). |
| `POST` | `/api/auth/login` | Public | Authenticate citizen; returns signed JWT. |
| `GET` | `/api/auth/me` | Bearer JWT | Returns current authenticated citizen profile. |
| `GET` | `/api/profile` | Bearer JWT | Retrieve full demographic profile from `citizen_profiles`. |
| `PUT` | `/api/profile` | Bearer JWT | Update socio-economic attributes in `citizen_profiles`. |
| `POST` | `/api/chat` | Bearer JWT | Conversational interaction; forwards to Python agent orchestrator. |
| `POST` | `/api/documents/upload` | Bearer JWT | Multipart document upload (max 10MB). |
| `GET` | `/api/documents` | Bearer JWT | List uploaded documents for authenticated citizen. |
| `GET` | `/api/schemes/search` | Bearer JWT | Search scheme clauses via RAG. |
| `POST` | `/api/eligibility/check` | Bearer JWT | Evaluate deterministic eligibility for a scheme. |
| `GET` | `/api/applications` | Bearer JWT | List scheme applications for authenticated citizen. |
| `POST` | `/api/applications` | Bearer JWT | Submit new application. |
| `GET` | `/api/applications/{id}` | Bearer JWT | Get application details and status timeline. |
| `GET` | `/api/health/live` | Public | Liveness probe. |
| `GET` | `/api/health/ready` | Public | Readiness probe (includes DB and Python AI service status). |

### 2. Spring Boot → Python AI Service Endpoints (`http://127.0.0.1:8000`)

*All endpoints require internal headers: `X-Internal-API-Key`, `X-Citizen-ID`, `X-Correlation-ID`.*

| Method | Endpoint | Handler | Description |
|---|---|---|---|
| `POST` | `/v1/agent/chat` | `AgentOrchestrator.run()` | Executes ReAct tool-calling loop for citizen. |
| `POST` | `/v1/needs/detect` | `NeedDetector.detect_needs()` | Direct multi-need detection. |
| `POST` | `/v1/schemes/search` | `SchemeRetriever.retrieve()` | Semantic vector search in Qdrant with citations. |
| `POST` | `/v1/schemes/discover` | `MySchemeAdapter.search_schemes()` | External government scheme discovery (M8). |
| `POST` | `/v1/eligibility/evaluate` | `EligibilityEngine.evaluate()` | Deterministic statutory eligibility assessment (M5). |
| `POST` | `/v1/documents/analyze` | `DocumentAI.analyze()` | Document OCR and structured fact extraction (M4). |
| `GET` | `/health/live` | Internal | Server liveness probe. |
| `GET` | `/health/ready` | Internal | Component readiness probe (MySQL, Qdrant, Embeddings, LLM). |

---

## 9. Comprehensive Testing & Regression Safety

### 1. Zero-Regression Invariant on M1–M8
- **The existing 228 passing tests must remain 100% green**.
- **M1 Retrieval Benchmark must remain at 100% Hit@1, Hit@3, Hit@5 and MRR 1.0000**.
- Zero modification to existing M1–M8 core logic files.

### 2. New Test Coverage for Milestone 9
- **Python AI API Tests (`tests/test_api_*.py`)**:
  - `test_api_auth_rejection`: Unauthenticated requests to `/v1/**` return 401.
  - `test_api_agent_chat`: Verifies `POST /v1/agent/chat` executes and propagates `X-Citizen-ID`.
  - `test_api_direct_endpoints`: Tests `/v1/needs/detect`, `/v1/schemes/search`, `/v1/eligibility/evaluate`, `/v1/documents/analyze`.
  - `test_api_health_liveness_readiness`: Verifies `/health/live` and `/health/ready` behavior under normal and degraded LLM states.
- **Spring Boot Tests (`backend/src/test/...`)**:
  - `JwtTokenProviderTest`: Unit test for token signing, expiration, and claims.
  - `AuthControllerTest`: MockMvc test for registration, login, and bad credentials.
  - `SecurityAccessTest`: Verifies IDOR prevention (Citizen A cannot read Citizen B's documents or applications).
  - `PythonAiServiceClientTest`: MockRestServiceServer test validating timeout handling, API key injection, and error translation.
- **React Frontend Tests (`frontend/src/...`)**:
  - Vitest component tests for Chat Window, Document Uploader, Scheme Explorer, and Application Tracker.
- **End-to-End System Test**:
  - Full end-to-end flow test: Register -> Login -> Chat -> Needs Detected -> Scheme Searched -> Document Uploaded -> Eligibility Assessed -> Application Submitted.

---

## 10. Phased Implementation Sequence

```
M9.1: Python FastAPI Layer ─────► M9.2: Spring Boot Skeleton & JPA
            │                                    │
            ▼                                    ▼
M9.3: Spring ↔ Python Client ───► M9.4: Authentication & Security (JWT)
            │                                    │
            ▼                                    ▼
M9.5: Chat & Multi-Need Flow ───► M9.6: Document Upload & AI Analysis
            │                                    │
            ▼                                    ▼
M9.7: Schemes & Eligibility ────► M9.8: React Frontend Application
            │                                    │
            └────────────────► M9.9: End-to-End Verification & Benchmark Check
```

1. **M9.1: Python FastAPI Layer**: Install `fastapi` and `uvicorn`, implement `src/api/` routes and schemas, add `tests/test_api_*.py`, verify 228 legacy tests pass.
2. **M9.2: Spring Boot Skeleton & Entities**: Initialize Maven project in `backend/` with Java 25. Create JPA entities mapping `citizen_ai_db` (with read-only projections for AI tables) and `users` table.
3. **M9.3: Spring ↔ Python Client**: Implement `PythonAiServiceClient` using Spring `RestClient` with timeout handling and correlation ID propagation.
4. **M9.4: Authentication & IDOR Protection**: Implement user registration, BCrypt password hashing, JWT filter, and IDOR access control.
5. **M9.5: Citizen Conversation & Needs Flow**: Implement `ChatController` and `NeedController` delegating to Python AI Service.
6. **M9.6: Document Upload & AI Analysis**: Implement file upload validation, SHA-256 computation, disk storage, and M4 delegation.
7. **M9.7: Schemes & Eligibility Endpoints**: Implement RAG scheme search and M5 deterministic eligibility evaluation endpoints.
8. **M9.8: React Frontend Application**: Initialize Vite + TypeScript + Tailwind CSS in `frontend/`, implement Citizen Portal UI.
9. **M9.9: End-to-End System Verification**: Run full integration test, run `pytest -q` (all passing), run `python -m src.evaluation.evaluate` (100% Hit@K, MRR 1.0000).

---

## 11. Acceptance Criteria

1. **Python API Layer**:
   - `http://127.0.0.1:8000/health/live` returns 200 OK.
   - `http://127.0.0.1:8000/health/ready` accurately reports component readiness.
   - All 228 legacy tests pass; all new API tests pass.
   - M1 Retrieval Benchmark remains 100% Hit@K and MRR 1.0000.
2. **Spring Boot Backend**:
   - Compiles cleanly on Java 25; boots on port 8080.
   - Enforces JWT authentication and strictly blocks IDOR attempts.
   - Acts as authoritative writer for `users`, `citizens`, `citizen_profiles`, and `applications`.
   - Never writes to AI-owned tables (`citizen_needs`, `document_extracted_fields`, `eligibility_assessments`).
3. **Document Flow**:
   - Successfully accepts PDF/image uploads under 10MB.
   - Stores file once; Python Document AI extracts key-value facts and updates database.
4. **Conversation Flow**:
   - Citizen query from React triggers `AgentOrchestrator` through Spring Boot.
   - Response contains natural language explanation, clickable citations (Page/Section), and detected need badges.
5. **Eligibility Evaluation**:
   - Deterministic statutory engine evaluates rules and displays pass/fail breakdown in UI.

---

## 12. Exact Files and Directories to be Created or Modified

### In `ai-service/`:
- **Modified**:
  - `requirements.txt` *(add `fastapi>=0.110.0`, `uvicorn>=0.30.0`)*
  - `src/config/settings.py` *(add `ai_service_host`, `ai_service_port`, `ai_service_internal_key`)*
- **New Files**:
  - `src/api/__init__.py`
  - `src/api/main.py`
  - `src/api/dependencies.py`
  - `src/api/routes/__init__.py`
  - `src/api/routes/health.py`
  - `src/api/routes/agent.py`
  - `src/api/routes/needs.py`
  - `src/api/routes/schemes.py`
  - `src/api/routes/eligibility.py`
  - `src/api/routes/documents.py`
  - `src/api/schemas/__init__.py`
  - `src/api/schemas/chat.py`
  - `src/api/schemas/needs.py`
  - `src/api/schemas/schemes.py`
  - `src/api/schemas/eligibility.py`
  - `src/api/schemas/documents.py`
  - `tests/test_api_routes.py`
  - `tests/test_api_security.py`

### In `backend/`:
- **New Files**:
  - `pom.xml` *(configured for Java 25)*
  - `mvnw`, `mvnw.cmd`, `.mvn/wrapper/maven-wrapper.properties`
  - `src/main/resources/application.yml`
  - `src/main/resources/schema.sql` *(creates `users` table if not present)*
  - `src/main/java/com/unifiedai/backend/BackendApplication.java`
  - `src/main/java/com/unifiedai/backend/config/SecurityConfig.java`
  - `src/main/java/com/unifiedai/backend/config/CorsConfig.java`
  - `src/main/java/com/unifiedai/backend/config/AiServiceClientConfig.java`
  - `src/main/java/com/unifiedai/backend/config/StorageConfig.java`
  - `src/main/java/com/unifiedai/backend/security/JwtTokenProvider.java`
  - `src/main/java/com/unifiedai/backend/security/JwtAuthenticationFilter.java`
  - `src/main/java/com/unifiedai/backend/security/CitizenUserDetails.java`
  - `src/main/java/com/unifiedai/backend/entity/UserEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/CitizenEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/CitizenProfileEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/ApplicationEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/ApplicationStatusHistoryEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/DocumentEntity.java`
  - `src/main/java/com/unifiedai/backend/entity/readonly/DocumentExtractedFieldProjection.java` *(read-only)*
  - `src/main/java/com/unifiedai/backend/entity/readonly/CitizenNeedProjection.java` *(read-only)*
  - `src/main/java/com/unifiedai/backend/entity/readonly/EligibilityAssessmentProjection.java` *(read-only)*
  - `src/main/java/com/unifiedai/backend/repository/UserRepository.java`
  - `src/main/java/com/unifiedai/backend/repository/CitizenRepository.java`
  - `src/main/java/com/unifiedai/backend/repository/CitizenProfileRepository.java`
  - `src/main/java/com/unifiedai/backend/repository/ApplicationRepository.java`
  - `src/main/java/com/unifiedai/backend/repository/DocumentRepository.java`
  - `src/main/java/com/unifiedai/backend/controller/AuthController.java`
  - `src/main/java/com/unifiedai/backend/controller/CitizenProfileController.java`
  - `src/main/java/com/unifiedai/backend/controller/ChatController.java`
  - `src/main/java/com/unifiedai/backend/controller/DocumentController.java`
  - `src/main/java/com/unifiedai/backend/controller/SchemeController.java`
  - `src/main/java/com/unifiedai/backend/controller/EligibilityController.java`
  - `src/main/java/com/unifiedai/backend/controller/ApplicationController.java`
  - `src/main/java/com/unifiedai/backend/controller/HealthController.java`
  - `src/main/java/com/unifiedai/backend/service/AuthService.java`
  - `src/main/java/com/unifiedai/backend/service/CitizenProfileService.java`
  - `src/main/java/com/unifiedai/backend/service/ChatService.java`
  - `src/main/java/com/unifiedai/backend/service/DocumentService.java`
  - `src/main/java/com/unifiedai/backend/service/SchemeService.java`
  - `src/main/java/com/unifiedai/backend/service/EligibilityService.java`
  - `src/main/java/com/unifiedai/backend/service/ApplicationService.java`
  - `src/main/java/com/unifiedai/backend/client/PythonAiServiceClient.java`
  - `src/test/java/com/unifiedai/backend/...` *(unit, controller, security tests)*

### In `frontend/`:
- **New Files**:
  - `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, `postcss.config.js`
  - `src/main.tsx`, `src/App.tsx`, `src/index.css`
  - `src/context/AuthContext.tsx`
  - `src/services/api.ts`
  - `src/components/chat/ChatWindow.tsx`
  - `src/components/chat/CitationChip.tsx`
  - `src/components/chat/NeedBadge.tsx`
  - `src/components/documents/DocumentUploader.tsx`
  - `src/components/documents/ExtractedFactCard.tsx`
  - `src/components/schemes/SchemeExplorer.tsx`
  - `src/components/eligibility/EligibilityCard.tsx`
  - `src/components/applications/ApplicationTracker.tsx`
  - `src/components/profile/ProfileEditor.tsx`

---

## 13. FINAL DECISIONS REQUIRING USER APPROVAL

Before beginning implementation, please review and approve these three architectural decisions:

1. **Application Table Ownership Transition**:
   - **Decision**: Spring Boot becomes the **sole authoritative writer** of `applications` and `application_status_history` at runtime. Python's M7 repository write methods are retained strictly for M7 test fixtures, while at runtime Python treats `applications` as read-only (via `ApplicationStatusTool`).
   - *Do you approve this transition policy?*

2. **AI-Owned Table Read-Only Projections**:
   - **Decision**: Spring Boot maps `citizen_needs`, `document_extracted_fields`, `eligibility_assessments`, and `government_api_audit_logs` strictly as **read-only projections** (`@Immutable` entities with no repository update/save methods), ensuring that Python remains the sole algorithmic writer.
   - *Do you approve enforcing read-only projections in Spring Boot for all AI-generated tables?*

3. **Java 25 Deterministic Selection**:
   - **Decision**: Standardize backend development deterministically on **Java 25** matching the verified host environment (`C:\Program Files\Java\jdk-25` and Apache Maven 3.9.14).
   - *Do you approve standardizing on Java 25?*
