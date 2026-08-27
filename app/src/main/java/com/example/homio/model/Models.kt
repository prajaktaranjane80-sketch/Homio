package com.example.homio.model

enum class GateStatus {
    APPROVED,
    IN_PROGRESS,
    PENDING,
    BLOCKED
}

enum class SubtaskSeverity {
    CRITICAL,
    HIGH,
    MEDIUM,
    LOW
}

data class GateSubtask(
    val id: String,
    val title: String,
    val severity: SubtaskSeverity,
    val isCompleted: Boolean = false,
    val completedAt: String? = null,
    val note: String? = null
)

data class ArchitectureGate(
    val id: String,
    val name: String,
    val phase: String,
    val status: GateStatus,
    val objective: String,
    val subtasks: List<GateSubtask>,
    val criteria: List<String>,
    val approvedAt: String? = null,
    val owner: String = "REOS Core Architecture"
)

enum class LeadSource {
    DIRECT_WEB,
    AI_CONVERSATIONAL,
    BROKER_NETWORK,
    SEO_INBOUND,
    CAMPAIGN_PORTAL
}

enum class LeadStatus {
    NEW_INCOMING,
    QUALIFIED,
    VERIFIED_ENQUIRY,
    VISIT_SCHEDULED,
    VISITED,
    NEGOTIATION,
    WON,
    LOST
}

data class Lead(
    val id: String,
    val name: String,
    val phone: String,
    val email: String,
    val budget: String,
    val preferredLocation: String,
    val interestedProject: String,
    val sourceChannel: LeadSource,
    val genuineScore: Int,
    val status: LeadStatus,
    val firstTouchAttributionHash: String,
    val builderAcknowledged: Boolean,
    val assignedAgent: String,
    val createdAt: String
)

data class Builder(
    val id: String,
    val name: String,
    val tier: String,
    val city: String,
    val activeProjects: Int,
    val standardCommissionPct: Double,
    val trustScore: Int,
    val reraRegistered: Boolean,
    val disputeCount: Int
)

data class Project(
    val id: String,
    val builderId: String,
    val builderName: String,
    val name: String,
    val location: String,
    val priceRange: String,
    val unitsTotal: Int,
    val unitsAvailable: Int,
    val commissionPct: Double,
    val projectType: String
)

enum class UnitStatus {
    AVAILABLE,
    BLOCKED,
    BOOKED,
    SOLD
}

data class UnitInventory(
    val id: String,
    val projectId: String,
    val projectName: String,
    val unitNumber: String,
    val tower: String,
    val type: String,
    val carpetAreaSqFt: Int,
    val price: Double,
    val status: UnitStatus,
    val commissionAmount: Double
)

enum class DealStage {
    TOKEN_PAID,
    AGREEMENT_SIGNED,
    REGISTRATION_DONE,
    COMMISSION_INVOICED,
    COMMISSION_DISBURSED,
    IN_DISPUTE
}

enum class ProtectionStatus {
    SECURED,
    ACKNOWLEDGED,
    UNDER_REVIEW,
    DISPUTE_FLAGGED
}

data class Deal(
    val id: String,
    val dealCode: String,
    val leadId: String,
    val leadName: String,
    val projectId: String,
    val projectName: String,
    val unitId: String,
    val unitNumber: String,
    val builderName: String,
    val dealValue: Double,
    val commissionPct: Double,
    val commissionAmount: Double,
    val stage: DealStage,
    val evidenceHash: String,
    val protectionStatus: ProtectionStatus,
    val updatedAt: String
)

enum class EvidenceType {
    SITE_VISIT_OTP,
    DIGITAL_CONSENT,
    BUILDER_TIMESTAMP_ACK,
    GPS_GEOFENCE_STAMP,
    BROKERAGE_AGREEMENT
}

data class EvidenceRecord(
    val id: String,
    val type: EvidenceType,
    val leadId: String,
    val dealId: String?,
    val title: String,
    val details: String,
    val sha256Hash: String,
    val verified: Boolean,
    val timestamp: String,
    val signer: String
)

enum class TripwireSeverity {
    CRITICAL,
    HIGH,
    MONITORING
}

data class TripwireRule(
    val id: String,
    val name: String,
    val category: String,
    val description: String,
    val isActive: Boolean,
    val triggersCount: Int,
    val severity: TripwireSeverity
)

data class AutonomyRole(
    val id: String,
    val name: String,
    val title: String,
    val responsibilities: List<String>,
    val activeTasks: Int
)

data class AuditLogEntry(
    val id: String,
    val timestamp: String,
    val actionType: String,
    val actor: String,
    val details: String,
    val hash: String
)

data class SystemStateSummary(
    val operatingMode: String,
    val systemTrustScore: Double,
    val stateIntegrityHash: String,
    val totalCommissionProtected: Double,
    val activeLeadsCount: Int,
    val genuineLeadsPct: Int,
    val verifiedInventoryCount: Int,
    val activeDealsCount: Int,
    val completedGatesCount: Int,
    val totalGatesCount: Int
)
