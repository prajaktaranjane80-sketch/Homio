package com.example.homio.model

object SampleData {

    val defaultGates: List<ArchitectureGate> = listOf(
        ArchitectureGate(
            id = "ARCH-001",
            name = "Lead Generation Layer",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Capture omnichannel buyer demand and establish initial attribution claim.",
            approvedAt = "2026-08-12T14:10:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Omnichannel intake endpoints", SubtaskSeverity.CRITICAL, true, "2026-08-12T14:10:00Z", "REST & Webhook intake verified"),
                GateSubtask("T02", "Deduplication & normalization engine", SubtaskSeverity.HIGH, true, "2026-08-12T14:12:00Z", "Phone/email fuzzy matcher armed")
            ),
            criteria = listOf(
                "Inbound leads receive instant timestamp and channel signature.",
                "Zero loss of attribution metadata during ingestion."
            )
        ),
        ArchitectureGate(
            id = "ARCH-002",
            name = "Lead Generation Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Automate lead capture pipeline with intent parsing and initial budget stratification.",
            approvedAt = "2026-08-12T15:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "NLP intent parsing model", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Budget-to-inventory match heuristics", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Budget tiers mapped to developer price slabs.")
        ),
        ArchitectureGate(
            id = "ARCH-003",
            name = "Lead Qualification + Genuine Lead Detection",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Distinguish genuine buyers from spam, bots, and duplicate broker inquiries.",
            approvedAt = "2026-08-12T16:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Behavioral clickstream & velocity scorer", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "SMS / WhatsApp OTP verification handshake", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Only leads with Genuine Score > 70 are routed to developer deals.")
        ),
        ArchitectureGate(
            id = "ARCH-004",
            name = "Lead Scoring + Routing + Attribution",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Route qualified leads to assigned international brokers and lock first-touch origin.",
            approvedAt = "2026-08-12T18:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Broker capacity & locality matching engine", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Cryptographic first-touch attribution ledger", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Lead attribution is tamper-proof and immutable.")
        ),
        ArchitectureGate(
            id = "ARCH-005",
            name = "Inventory Acquisition Layer",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Standardize direct ingestion of builder inventory and floorplans.",
            approvedAt = "2026-08-13T09:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Builder API & bulk feed sync adapters", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "RERA & municipal clearance verification", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Every unit is linked to a verified developer RERA ID.")
        ),
        ArchitectureGate(
            id = "ARCH-006",
            name = "Inventory Acquisition Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Manage live inventory statuses (available, blocked, sold) in real-time.",
            approvedAt = "2026-08-13T11:20:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Unit status state machine", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Concurrent booking lock mechanism", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Double-booking prevented across distributed channels.")
        ),
        ArchitectureGate(
            id = "ARCH-007",
            name = "Builder Onboarding + Project Acquisition",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Streamline institutional builder KYC and legal brokerage agreement execution.",
            approvedAt = "2026-08-13T14:15:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Digital brokerage commission contract signer", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Builder escrow & payout terms registry", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Signed commission slab contract stored in immutable registry.")
        ),
        ArchitectureGate(
            id = "ARCH-008",
            name = "Multi-Project / Flat / Plot Inventory",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Hierarchical data representation of Towers, Floors, Units, Villas and Land Parcels.",
            approvedAt = "2026-08-13T17:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Hierarchical inventory tree schema", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Custom floorplan coordinate visualizer", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Supports multi-phase township and single-unit tracking seamlessly.")
        ),
        ArchitectureGate(
            id = "ARCH-009",
            name = "Communication Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Multi-channel automated communication (WhatsApp, Email, In-app) with audit trail.",
            approvedAt = "2026-08-14T10:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "WhatsApp Business API & Twilio integration", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Automated appointment & visit reminder queues", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("All customer-agent messages timestamped for dispute evidence.")
        ),
        ArchitectureGate(
            id = "ARCH-010",
            name = "Lead Ownership Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Enforce strict broker lead ownership window (90-180 days) with auto-renewal.",
            approvedAt = "2026-08-14T12:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Ownership validity countdown timers", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Anti-poaching conflict resolver", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Protects broker from unauthorized lead stealing by internal or external reps.")
        ),
        ArchitectureGate(
            id = "ARCH-011",
            name = "Deal Ownership Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Bind buyer, broker, builder, and unit into a locked immutable transaction contract.",
            approvedAt = "2026-08-14T14:45:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Deal creation pipeline with 4-way cryptographic binding", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Milestone stage progression engine", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Deal cannot be completed without verified evidence chain.")
        ),
        ArchitectureGate(
            id = "ARCH-012",
            name = "Commission Protection Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Automate commission invoicing, dispute detection, and escrow disbursement defense.",
            approvedAt = "2026-08-14T16:20:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Dynamic commission calculation breakdown", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Automated builder invoice generator & tracking", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Dispute protection triggers automatic evidence package delivery.")
        ),
        ArchitectureGate(
            id = "ARCH-013",
            name = "Customer Attribution + Builder Acknowledgement",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Generate immediate builder acknowledgment upon lead registration and site visit booking.",
            approvedAt = "2026-08-14T18:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Builder webhook dispatch on lead registration", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Cryptographic digital receipt signed by builder CRM", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Guarantees builder cannot claim direct walk-in if registered in HOMIO prior.")
        ),
        ArchitectureGate(
            id = "ARCH-014",
            name = "Evidence / Consent / Visit / Enquiry Proof Layer",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Collect GPS geofenced site visit check-ins, OTP confirmation, and digital consent.",
            approvedAt = "2026-08-15T09:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "GPS geofence radius check (100m accuracy)", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Buyer OTP verify on project sales desk arrival", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Evidence ledger maintains SHA-256 hash chains of all customer proofs.")
        ),
        ArchitectureGate(
            id = "ARCH-015",
            name = "Trust Score Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Continuously calculate trust scores for developers, brokers, and leads.",
            approvedAt = "2026-08-15T11:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Builder payout timeliness rating algorithm", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Broker integrity & compliance index", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Low trust score developers restricted from automated lead routing.")
        ),
        ArchitectureGate(
            id = "ARCH-016",
            name = "Fraud Detection Algorithm v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Prevent fake visits, ghost leads, duplicate commission claiming, and collusion.",
            approvedAt = "2026-08-15T13:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Anomaly detection on lead submission velocity", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "GPS spoofing & proxy detection", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Suspicious activity raises automated tripwire alert.")
        ),
        ArchitectureGate(
            id = "ARCH-017",
            name = "Governance Engine v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Enforce operational compliance, regulatory rules, and internal policy tripwires.",
            approvedAt = "2026-08-15T14:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Policy evaluator & immutable audit logger", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Role-based action permission gates", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Zero unauthorized state mutations allowed without audit record.")
        ),
        ArchitectureGate(
            id = "ARCH-018",
            name = "Preventive Error + Policy Enforcement Layer",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Pre-execution firewall stopping illegal state transitions before execution.",
            approvedAt = "2026-08-15T16:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Pre-execution invariant checker", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Tripwire circuit breakers for high-risk mutations", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("All destructive or financial mutations blocked if invariant fails.")
        ),
        ArchitectureGate(
            id = "ARCH-019",
            name = "AI Agent Layer v1.0",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Autonomous agent roles for Lead Nurturing, Valuation, and Deal Coordination.",
            approvedAt = "2026-08-15T17:15:00Z",
            subtasks = listOf(
                GateSubtask("T01", "AI conversational agent for 24/7 lead qualification", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Automated broker matching assistant", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("AI agents operate within strict guardrails and cannot commit financial obligations.")
        ),
        ArchitectureGate(
            id = "ARCH-020",
            name = "SEO + Data Intelligence Layer",
            phase = "PHASE_1",
            status = GateStatus.APPROVED,
            objective = "Organic demand capture, localized micro-market pricing intelligence, and trend analytics.",
            approvedAt = "2026-08-15T18:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Real-time micro-market price indexing", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Automated localized property page generator", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Market intelligence feeds directly into lead budget recommendation engine.")
        ),
        ArchitectureGate(
            id = "ARCH-021",
            name = "Database DNA Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Canonical relational model with strict tenant isolation and audit trails.",
            approvedAt = "2026-08-15T18:10:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Entity-relationship mapping with tenant_id isolation", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Immutable append-only event ledger table", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Strict referential integrity on deal, lead, and inventory models.")
        ),
        ArchitectureGate(
            id = "ARCH-022",
            name = "Event-Driven Database Design v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Event sourcing for all deal status transitions and commission payouts.",
            approvedAt = "2026-08-15T18:15:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Domain event schema definition (Kafka / Postgres WAL)", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Event replay and state reconstruction mechanism", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Historical state can be deterministically replayed at any timestamp.")
        ),
        ArchitectureGate(
            id = "ARCH-023",
            name = "Search Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Fast multi-facet inventory search and vector similarity property matching.",
            approvedAt = "2026-08-15T18:20:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Elastic / OpenSearch index for inventory queries", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Vector embeddings for buyer lifestyle matching", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Sub-50ms search latency across 500,000+ units.")
        ),
        ArchitectureGate(
            id = "ARCH-024",
            name = "API Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "OpenAPI 3.1 compliant REST & GraphQL gateway with rate limiting and JWT auth.",
            approvedAt = "2026-08-15T18:25:00Z",
            subtasks = listOf(
                GateSubtask("T01", "API Gateway & OAuth2 / mTLS token verification", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Rate limiter per tenant & API key tier", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Zero unauthorized API access allowed.")
        ),
        ArchitectureGate(
            id = "ARCH-025",
            name = "Microservice Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Decoupled bounded contexts: LeadSvc, InventorySvc, DealSvc, TrustSvc, PayoutSvc.",
            approvedAt = "2026-08-15T18:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Bounded context boundaries and gRPC service contracts", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Circuit breaker and fallback handlers", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Failure in one service does not cascade to lead capture.")
        ),
        ArchitectureGate(
            id = "ARCH-026",
            name = "Data Warehouse Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "OLAP pipeline for brokerage analytics, conversion funnels, and commission forecast.",
            approvedAt = "2026-08-15T18:35:00Z",
            subtasks = listOf(
                GateSubtask("T01", "CDC pipeline from transactional database to BigQuery", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Star schema for sales & commission forecasting", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Daily aggregated analytics ready by 06:00 UTC.")
        ),
        ArchitectureGate(
            id = "ARCH-027",
            name = "Analytics Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Executive dashboards for pipeline velocity, lead conversion rate, and commission yield.",
            approvedAt = "2026-08-15T18:40:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Real-time telemetry stream processor", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Executive KPI calculation algorithms", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Live metrics updated within 5 seconds of event occurrence.")
        ),
        ArchitectureGate(
            id = "ARCH-028",
            name = "Security Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Zero Trust security model, AES-256 encryption at rest, TLS 1.3 in transit, KMS key rotation.",
            approvedAt = "2026-08-15T18:45:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Envelope encryption for PII buyer contacts", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Automated vulnerability scanner & tripwire monitoring", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("SOC2 and GDPR compliance criteria satisfied.")
        ),
        ArchitectureGate(
            id = "ARCH-029",
            name = "DevOps Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Kubernetes infrastructure, GitOps deployment with ArgoCD, multi-region failover.",
            approvedAt = "2026-08-15T18:50:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Terraform infrastructure-as-code manifests", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Blue/Green zero-downtime deployment pipelines", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("99.99% system availability SLA.")
        ),
        ArchitectureGate(
            id = "ARCH-030",
            name = "AI Infrastructure Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Dedicated model serving cluster, context compilation memory store, and prompt guardrails.",
            approvedAt = "2026-08-15T18:55:00Z",
            subtasks = listOf(
                GateSubtask("T01", "LLM inference gateway with latency caching", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Prompt injection & hallucination firewall", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Zero unauthorized model calls outside budget limit.")
        ),
        ArchitectureGate(
            id = "ARCH-031",
            name = "Global Multi-Tenant Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Multi-country support (India, UAE, UK, Singapore, US) with currency & legal localization.",
            approvedAt = "2026-08-15T19:00:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Multi-currency converter (INR, AED, USD, GBP)", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Jurisdiction legal compliance rulebook per country", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Data residency enforced per regional jurisdiction.")
        ),
        ArchitectureGate(
            id = "ARCH-032",
            name = "International Brokerage Operating Model",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Cross-border NRI & foreign investor property syndication and legal escrow flows.",
            approvedAt = "2026-08-15T19:10:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Cross-border KYC and AML verification bridge", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Multi-jurisdiction commission split agreements", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("AML screening verified for 100% of international transactions.")
        ),
        ArchitectureGate(
            id = "ARCH-033",
            name = "Builder–Broker–Customer Relationship Protection",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Tripartite relationship locking with cryptographic audit certificate.",
            approvedAt = "2026-08-15T19:20:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Tripartite handshake protocol", SubtaskSeverity.CRITICAL, true),
                GateSubtask("T02", "Automated dispute arbitration evidence package", SubtaskSeverity.HIGH, true)
            ),
            criteria = listOf("Builder cannot bypass broker once digital certificate is issued.")
        ),
        ArchitectureGate(
            id = "ARCH-034",
            name = "Commission Lifecycle + Dispute Protection",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "End-to-end lifecycle from deal booking to bank escrow settlement with automated penalty clauses.",
            approvedAt = "2026-08-15T19:30:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Milestone payment triggers", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Late payout interest calculator", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Commission tracked transparently in real-time by broker.")
        ),
        ArchitectureGate(
            id = "ARCH-035",
            name = "Automation-First Customer Journey",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "One-click verification, instant WhatsApp brochures, virtual 3D tour bookings.",
            approvedAt = "2026-08-15T19:40:00Z",
            subtasks = listOf(
                GateSubtask("T01", "One-click interactive digital passbook", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Self-service visit scheduling calendar", SubtaskSeverity.MEDIUM, true)
            ),
            criteria = listOf("Time-to-qualification reduced to under 3 minutes.")
        ),
        ArchitectureGate(
            id = "ARCH-036",
            name = "Business Operating Modes Architecture v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Dynamic switching between Direct Brokerage, Aggregator Hub, Builder SaaS, and Franchise.",
            approvedAt = "2026-08-15T19:45:00Z",
            subtasks = listOf(
                GateSubtask("T01", "Operating mode feature-flag coordinator", SubtaskSeverity.HIGH, true),
                GateSubtask("T02", "Revenue-share formula matrix", SubtaskSeverity.CRITICAL, true)
            ),
            criteria = listOf("Mode changes execute without system restart.")
        ),
        ArchitectureGate(
            id = "ARCH-037",
            name = "Database Final Schema Design v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Finalize the production-grade database schema from the approved Database DNA.",
            approvedAt = "2026-08-15T18:21:35Z",
            subtasks = listOf(
                GateSubtask("T01", "Inventory canonical entities and bounded contexts", SubtaskSeverity.CRITICAL, true, "2026-08-15T16:44:40Z", "Entities verified"),
                GateSubtask("T02", "Define final tables and source-of-truth ownership", SubtaskSeverity.CRITICAL, true, "2026-08-15T16:49:12Z", "Tables locked"),
                GateSubtask("T03", "Define keys relationships and referential rules", SubtaskSeverity.CRITICAL, true, "2026-08-15T16:50:23Z", "FKs verified"),
                GateSubtask("T04", "Define tenant isolation and authorization fields", SubtaskSeverity.CRITICAL, true, "2026-08-15T16:51:05Z", "Tenant isolation enforced"),
                GateSubtask("T05", "Define indexes uniqueness and critical constraints", SubtaskSeverity.HIGH, true, "2026-08-15T16:51:54Z", "Indexes tuned"),
                GateSubtask("T06", "Define event and audit persistence model", SubtaskSeverity.HIGH, true, "2026-08-15T16:53:25Z", "Audit persistence verified"),
                GateSubtask("T07", "Define retention archival and recovery rules", SubtaskSeverity.HIGH, true, "2026-08-15T16:55:04Z", "Archival verified"),
                GateSubtask("T08", "Define schema migration and versioning strategy", SubtaskSeverity.HIGH, true, "2026-08-15T17:33:49Z", "Migrations structured"),
                GateSubtask("T09", "Run normalization and duplication review", SubtaskSeverity.CRITICAL, true, "2026-08-15T17:57:15Z", "3NF normalization verified"),
                GateSubtask("T10", "Run security privacy and performance review", SubtaskSeverity.CRITICAL, true, "2026-08-15T18:13:55Z", "Security scan clean"),
                GateSubtask("T11", "Final schema freeze approval", SubtaskSeverity.CRITICAL, true, "2026-08-15T18:20:36Z", "Schema locked")
            ),
            criteria = listOf(
                "Every canonical business entity has one authoritative source of truth.",
                "Lead, deal, inventory, trust, fraud, governance and commission relationships are traceable.",
                "Tenant isolation is enforceable at database level."
            )
        ),
        ArchitectureGate(
            id = "ARCH-038",
            name = "Technology Stack Lock v1.0",
            phase = "PHASE_2",
            status = GateStatus.APPROVED,
            objective = "Freeze the implementation technology stack with explicit reasons and no unnecessary complexity.",
            approvedAt = "2026-08-15T19:50:05Z",
            subtasks = listOf(
                GateSubtask("T01", "Define frontend and runtime stack", SubtaskSeverity.CRITICAL, true, "2026-08-15T19:48:57Z", "Jetpack Compose / Kotlin Android locked"),
                GateSubtask("T02", "Define backend and service runtime stack", SubtaskSeverity.CRITICAL, true, "2026-08-15T19:48:58Z", "Kotlin Microservices & REST/gRPC"),
                GateSubtask("T03", "Define database and data infrastructure", SubtaskSeverity.CRITICAL, true, "2026-08-15T19:48:58Z", "PostgreSQL & Room local store"),
                GateSubtask("T04", "Define event bus cache and background jobs", SubtaskSeverity.HIGH, true, "2026-08-15T19:48:58Z", "Redis & Kafka event streams"),
                GateSubtask("T05", "Define search vector and AI infrastructure", SubtaskSeverity.HIGH, true, "2026-08-15T19:48:59Z", "OpenSearch & Gemini API infrastructure"),
                GateSubtask("T06", "Define cloud deployment and container strategy", SubtaskSeverity.HIGH, true, "2026-08-15T19:48:59Z", "Kubernetes & Cloud Run"),
                GateSubtask("T07", "Define observability and security tooling", SubtaskSeverity.HIGH, true, "2026-08-15T19:49:00Z", "OpenTelemetry & Zero Trust KMS"),
                GateSubtask("T08", "Run cost scalability and vendor-lock review", SubtaskSeverity.CRITICAL, true, "2026-08-15T19:49:20Z", "Cost review approved"),
                GateSubtask("T09", "Freeze technology decision record", SubtaskSeverity.CRITICAL, true, "2026-08-15T19:50:05Z", "Decision record locked")
            ),
            criteria = listOf(
                "Every production component has a defined purpose and owner.",
                "Stack supports multi-tenancy and event-driven services.",
                "No unnecessary technology is introduced."
            )
        ),
        ArchitectureGate(
            id = "ARCH-039",
            name = "Master Blueprint v1.0",
            phase = "PHASE_2",
            status = GateStatus.IN_PROGRESS,
            objective = "Assemble all approved architecture into one machine-readable implementation contract.",
            approvedAt = null,
            subtasks = listOf(
                GateSubtask("T01", "Assemble business architecture registry", SubtaskSeverity.CRITICAL, true, "2026-08-16T12:13:21Z", "Business registry compiled"),
                GateSubtask("T02", "Assemble technical architecture registry", SubtaskSeverity.CRITICAL, true, "2026-08-16T14:28:02Z", "Technical architecture compiled"),
                GateSubtask("T03", "Assemble database event and API contracts", SubtaskSeverity.CRITICAL, true, "2026-08-16T21:31:37Z", "Contracts validated"),
                GateSubtask("T04", "Assemble security governance and approval rules", SubtaskSeverity.CRITICAL, true, "2026-08-17T02:56:00Z", "Security rules locked"),
                GateSubtask("T05", "Assemble implementation dependency graph", SubtaskSeverity.CRITICAL, true, "2026-08-17T14:37:54Z", "Graph generated"),
                GateSubtask("T06", "Run architecture consistency and duplicate review", SubtaskSeverity.CRITICAL, true, "2026-08-17T14:51:07Z", "Zero duplicate verified"),
                GateSubtask("T07", "Generate repository implementation map", SubtaskSeverity.CRITICAL, false, null, "Pending final Android compilation"),
                GateSubtask("T08", "Freeze Master Blueprint", SubtaskSeverity.CRITICAL, false, null, "Awaiting gate completion signoff")
            ),
            criteria = listOf(
                "All approved architecture gates are represented.",
                "No unresolved architecture conflicts remain.",
                "Dependencies and execution order are machine-readable.",
                "Security and governance controls are preserved.",
                "Master Blueprint is versioned and frozen."
            )
        )
    )

    val defaultBuilders = listOf(
        Builder("BLD-01", "Emaar Properties", "A_PLUS", "Dubai / International", 14, 2.5, 98, true, 0),
        Builder("BLD-02", "Sobha Realty", "A_PLUS", "Dubai & Mumbai", 9, 3.0, 96, true, 0),
        Builder("BLD-03", "Prestige Estates", "TIER_1", "Bengaluru & Mumbai", 22, 2.0, 94, true, 1),
        Builder("BLD-04", "Godrej Properties", "TIER_1", "Pan-India", 18, 2.0, 95, true, 0),
        Builder("BLD-05", "DLF Luxury", "A_PLUS", "Gurugram / NCR", 8, 2.25, 97, true, 0)
    )

    val defaultProjects = listOf(
        Project("PRJ-01", "BLD-01", "Emaar Properties", "Emaar Beachfront Horizon", "Dubai Marina Coast", "$850K - $3.4M", 280, 42, 2.5, "Luxury High-Rise"),
        Project("PRJ-02", "BLD-02", "Sobha Realty", "Sobha Verde Forest View", "JLT District, Dubai", "$620K - $2.1M", 195, 28, 3.0, "Luxury High-Rise"),
        Project("PRJ-03", "BLD-03", "Prestige Estates", "Prestige Kingfisher Boulevard", "Central Bengaluru", "₹3.8 Cr - ₹9.5 Cr", 160, 19, 2.0, "Ultra Luxury Residences"),
        Project("PRJ-04", "BLD-04", "Godrej Properties", "Godrej Emerald Bayfront", "Bandra, Mumbai", "₹4.5 Cr - ₹14.0 Cr", 120, 14, 2.0, "Sea-facing Towers"),
        Project("PRJ-05", "BLD-05", "DLF Luxury", "The Dahlias Super Luxury", "Golf Course Rd, Gurgaon", "₹18.0 Cr - ₹45.0 Cr", 60, 8, 2.25, "Super Luxury Condos")
    )

    val defaultUnits = listOf(
        UnitInventory("UNT-101", "PRJ-01", "Emaar Beachfront Horizon", "Unit 2404", "Tower A", "3 BHK Panoramic", 2150, 1450000.0, UnitStatus.AVAILABLE, 36250.0),
        UnitInventory("UNT-102", "PRJ-01", "Emaar Beachfront Horizon", "Unit 3801", "Tower A", "4 BHK Penthouse", 3800, 2950000.0, UnitStatus.BLOCKED, 73750.0),
        UnitInventory("UNT-201", "PRJ-02", "Sobha Verde Forest View", "Unit 1208", "Tower Green", "2 BHK Premium", 1450, 780000.0, UnitStatus.AVAILABLE, 23400.0),
        UnitInventory("UNT-301", "PRJ-03", "Prestige Kingfisher Boulevard", "Unit 0902", "Wing C", "3 BHK + Study", 2650, 620000.0, UnitStatus.BOOKED, 12400.0),
        UnitInventory("UNT-401", "PRJ-04", "Godrej Emerald Bayfront", "Unit 1804", "Tower Zenith", "4 BHK Sea View", 3200, 980000.0, UnitStatus.AVAILABLE, 19600.0),
        UnitInventory("UNT-501", "PRJ-05", "The Dahlias Super Luxury", "Unit 0401", "Club Tower", "5 BHK Signature Suite", 6800, 3200000.0, UnitStatus.AVAILABLE, 72000.0)
    )

    val defaultLeads = listOf(
        Lead(
            id = "LED-8091",
            name = "Rohan Varma",
            phone = "+971 50 892 4190",
            email = "rohan.varma@capitalgrp.ae",
            budget = "$1.2M - $1.8M",
            preferredLocation = "Dubai Marina / Coastal",
            interestedProject = "Emaar Beachfront Horizon",
            sourceChannel = LeadSource.AI_CONVERSATIONAL,
            genuineScore = 96,
            status = LeadStatus.VISIT_SCHEDULED,
            firstTouchAttributionHash = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            builderAcknowledged = true,
            assignedAgent = "Sarah Al-Mansoor (Dubai Desk)",
            createdAt = "2026-08-25T11:30:00Z"
        ),
        Lead(
            id = "LED-8092",
            name = "Vikram & Ananya Singhania",
            phone = "+91 98200 44812",
            email = "vikram.singhania@indtech.co.in",
            budget = "₹6.0 Cr - ₹8.5 Cr",
            preferredLocation = "Bandra West / Worli",
            interestedProject = "Godrej Emerald Bayfront",
            sourceChannel = LeadSource.DIRECT_WEB,
            genuineScore = 92,
            status = LeadStatus.NEGOTIATION,
            firstTouchAttributionHash = "sha256:8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
            builderAcknowledged = true,
            assignedAgent = "Aditya Malhotra (Mumbai Prime)",
            createdAt = "2026-08-26T09:15:00Z"
        ),
        Lead(
            id = "LED-8093",
            name = "Alexander Bennett",
            phone = "+44 7700 900142",
            email = "a.bennett@londonholdings.uk",
            budget = "$2.5M - $3.5M",
            preferredLocation = "Dubai Waterfront Luxury",
            interestedProject = "Sobha Verde Forest View",
            sourceChannel = LeadSource.BROKER_NETWORK,
            genuineScore = 88,
            status = LeadStatus.VERIFIED_ENQUIRY,
            firstTouchAttributionHash = "sha256:ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            builderAcknowledged = true,
            assignedAgent = "Marcus Sterling (International Hub)",
            createdAt = "2026-08-26T14:40:00Z"
        ),
        Lead(
            id = "LED-8094",
            name = "Kavita Narayanan",
            phone = "+91 99401 22890",
            email = "kavita.n@zenithventures.io",
            budget = "₹4.0 Cr - ₹5.0 Cr",
            preferredLocation = "Central Bengaluru",
            interestedProject = "Prestige Kingfisher Boulevard",
            sourceChannel = LeadSource.SEO_INBOUND,
            genuineScore = 94,
            status = LeadStatus.VISITED,
            firstTouchAttributionHash = "sha256:5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            builderAcknowledged = true,
            assignedAgent = "Pooja Hegde (BLR North)",
            createdAt = "2026-08-26T16:00:00Z"
        ),
        Lead(
            id = "LED-8095",
            name = "Web Visitor #3194 (Flagged Bot)",
            phone = "+1 555 019 2831",
            email = "spam_test@throwaway.net",
            budget = "Unspecified",
            preferredLocation = "Unknown",
            interestedProject = "Emaar Beachfront Horizon",
            sourceChannel = LeadSource.CAMPAIGN_PORTAL,
            genuineScore = 18,
            status = LeadStatus.NEW_INCOMING,
            firstTouchAttributionHash = "sha256:3a7bd3e2360a3d29eea436fcfb7e44c735d117c42d1c1835420b6b9942dd4f1b",
            builderAcknowledged = false,
            assignedAgent = "Unassigned (Quarantined)",
            createdAt = "2026-08-27T03:10:00Z"
        )
    )

    val defaultDeals = listOf(
        Deal(
            id = "DEL-501",
            dealCode = "HOMIO-DXB-2026-0089",
            leadId = "LED-8091",
            leadName = "Rohan Varma",
            projectId = "PRJ-01",
            projectName = "Emaar Beachfront Horizon",
            unitId = "UNT-101",
            unitNumber = "Unit 2404 (Tower A)",
            builderName = "Emaar Properties",
            dealValue = 1450000.0,
            commissionPct = 2.5,
            commissionAmount = 36250.0,
            stage = DealStage.TOKEN_PAID,
            evidenceHash = "sha256:1a84f3235b2e4f7e2c98d6f5431872a912e5c89146f31dbb8918237649a12903",
            protectionStatus = ProtectionStatus.SECURED,
            updatedAt = "2026-08-26T18:30:00Z"
        ),
        Deal(
            id = "DEL-502",
            dealCode = "HOMIO-MUM-2026-0042",
            leadId = "LED-8092",
            leadName = "Vikram & Ananya Singhania",
            projectId = "PRJ-04",
            projectName = "Godrej Emerald Bayfront",
            unitId = "UNT-401",
            unitNumber = "Unit 1804 (Tower Zenith)",
            builderName = "Godrej Properties",
            dealValue = 980000.0,
            commissionPct = 2.0,
            commissionAmount = 19600.0,
            stage = DealStage.AGREEMENT_SIGNED,
            evidenceHash = "sha256:4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
            protectionStatus = ProtectionStatus.SECURED,
            updatedAt = "2026-08-27T01:15:00Z"
        ),
        Deal(
            id = "DEL-503",
            dealCode = "HOMIO-BLR-2026-0031",
            leadId = "LED-8094",
            leadName = "Kavita Narayanan",
            projectId = "PRJ-03",
            projectName = "Prestige Kingfisher Boulevard",
            unitId = "UNT-301",
            unitNumber = "Unit 0902 (Wing C)",
            builderName = "Prestige Estates",
            dealValue = 620000.0,
            commissionPct = 2.0,
            commissionAmount = 12400.0,
            stage = DealStage.COMMISSION_INVOICED,
            evidenceHash = "sha256:ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d",
            protectionStatus = ProtectionStatus.ACKNOWLEDGED,
            updatedAt = "2026-08-27T04:20:00Z"
        )
    )

    val defaultEvidence = listOf(
        EvidenceRecord(
            id = "EVD-901",
            type = EvidenceType.SITE_VISIT_OTP,
            leadId = "LED-8091",
            dealId = "DEL-501",
            title = "Geofenced Site Visit OTP Verification",
            details = "Buyer visited Emaar Beachfront site office. OTP #8491 confirmed by Sales Desk Manager.",
            sha256Hash = "sha256:7d8a2b5e9f1a0c4e7235b2e4f7e2c98d6f5431872a912e5c89146f31dbb89182",
            verified = true,
            timestamp = "2026-08-26T14:12:00Z",
            signer = "Emaar Sales Director & REOS Geofence Guard"
        ),
        EvidenceRecord(
            id = "EVD-902",
            type = EvidenceType.BUILDER_TIMESTAMP_ACK,
            leadId = "LED-8092",
            dealId = "DEL-502",
            title = "Builder CRM Attribution Certificate",
            details = "Godrej Properties Enterprise API confirmed first-touch lead registration by HOMIO.",
            sha256Hash = "sha256:b10a6d83961dd3c1ac88b59b2dc327aa4e3b0c44298fc1c149afbf4c8996fb92",
            verified = true,
            timestamp = "2026-08-26T16:45:00Z",
            signer = "Godrej Automated Integration Bridge"
        ),
        EvidenceRecord(
            id = "EVD-903",
            type = EvidenceType.DIGITAL_CONSENT,
            leadId = "LED-8094",
            dealId = "DEL-503",
            title = "Customer Representation Mandate",
            details = "Digital signature on buyer representation mandate with OTP dual-factor authorization.",
            sha256Hash = "sha256:ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            verified = true,
            timestamp = "2026-08-26T17:20:00Z",
            signer = "Kavita Narayanan (Buyer Client)"
        )
    )

    val defaultTripwires = listOf(
        TripwireRule(
            id = "TRP-01",
            name = "Commission Poaching Defense",
            category = "COMMISSION_PROTECTION",
            description = "Triggers immediate freeze and alert if builder CRM reports duplicate customer under different agent within 180 days of HOMIO registration.",
            isActive = true,
            triggersCount = 0,
            severity = TripwireSeverity.CRITICAL
        ),
        TripwireRule(
            id = "TRP-02",
            name = "Pre-Execution Gate Invariant Firewall",
            category = "PRE_EXEC_GATE",
            description = "Blocks any state transition or database mutation if unapproved subtasks or failing acceptance criteria exist.",
            isActive = true,
            triggersCount = 2,
            severity = TripwireSeverity.CRITICAL
        ),
        TripwireRule(
            id = "TRP-03",
            name = "GPS Spoofing & Ghost Visit Isolator",
            category = "FRAUD_ISOLATION",
            description = "Rejects site visit check-in proofs if device telemetry exhibits mock location providers or impossible speed jumps.",
            isActive = true,
            triggersCount = 1,
            severity = TripwireSeverity.HIGH
        ),
        TripwireRule(
            id = "TRP-04",
            name = "Unauthorized Architecture Mutation Guard",
            category = "OWNERSHIP_TAMPERING",
            description = "Maintains state.json SHA-256 integrity hash. Any manual filesystem edits without Control Center signoff trigger immediate rollback.",
            isActive = true,
            triggersCount = 0,
            severity = TripwireSeverity.CRITICAL
        )
    )

    val defaultRoles = listOf(
        AutonomyRole("ROL-01", "Architect", "System Boundary & Topology Guardian", listOf("System boundaries", "Source-of-truth invariants", "Dependency enforcement", "Architecture gate signoff"), 2),
        AutonomyRole("ROL-02", "Researcher", "Market & Micro-Pricing Intelligence", listOf("Current property market facts", "Developer financial stability checks", "RERA compliance checks"), 1),
        AutonomyRole("ROL-03", "Red Team", "Adversarial & Abuse Surface Tester", listOf("Attack surface analysis", "Commission bypass simulations", "Ghost lead penetration testing"), 3),
        AutonomyRole("ROL-04", "Implementer", "Kernel Engine & Adapter Executor", listOf("Autonomous code changes", "Continuous unit tests", "Integration lock verification"), 4),
        AutonomyRole("ROL-05", "Reviewer", "Invariant & Diff Consistency Evaluator", listOf("Semantic diff review", "Invariant checking", "Regression prevention"), 2),
        AutonomyRole("ROL-06", "Release Guardian", "Preflight & Safety Firewall Controller", listOf("Preflight verification", "Tripwire circuit arming", "Approval gate readiness"), 1)
    )
}
