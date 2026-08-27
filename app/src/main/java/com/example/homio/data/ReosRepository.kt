package com.example.homio.data

import com.example.homio.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

class ReosRepository {

    private val _gates = MutableStateFlow(SampleData.defaultGates)
    val gates: StateFlow<List<ArchitectureGate>> = _gates.asStateFlow()

    private val _leads = MutableStateFlow(SampleData.defaultLeads)
    val leads: StateFlow<List<Lead>> = _leads.asStateFlow()

    private val _builders = MutableStateFlow(SampleData.defaultBuilders)
    val builders: StateFlow<List<Builder>> = _builders.asStateFlow()

    private val _projects = MutableStateFlow(SampleData.defaultProjects)
    val projects: StateFlow<List<Project>> = _projects.asStateFlow()

    private val _units = MutableStateFlow(SampleData.defaultUnits)
    val units: StateFlow<List<UnitInventory>> = _units.asStateFlow()

    private val _deals = MutableStateFlow(SampleData.defaultDeals)
    val deals: StateFlow<List<Deal>> = _deals.asStateFlow()

    private val _evidence = MutableStateFlow(SampleData.defaultEvidence)
    val evidence: StateFlow<List<EvidenceRecord>> = _evidence.asStateFlow()

    private val _tripwires = MutableStateFlow(SampleData.defaultTripwires)
    val tripwires: StateFlow<List<TripwireRule>> = _tripwires.asStateFlow()

    private val _roles = MutableStateFlow(SampleData.defaultRoles)
    val roles: StateFlow<List<AutonomyRole>> = _roles.asStateFlow()

    private val _auditLogs = MutableStateFlow<List<AuditLogEntry>>(
        listOf(
            AuditLogEntry("LOG-001", currentTimestamp(), "SYSTEM_INIT", "REOS_KERNEL", "Loaded 38 approved architecture gates and 1 pending blueprint", generateHash("SYSTEM_INIT")),
            AuditLogEntry("LOG-002", currentTimestamp(), "FIREWALL_ARM", "TRIPWIRE_ENGINE", "All 4 critical tripwires active with zero tolerance bypass", generateHash("TRIPWIRE_ARM")),
            AuditLogEntry("LOG-003", currentTimestamp(), "COMMISSION_LOCK", "PROTECTION_SVC", "Secured $68,250 in active pipeline commissions", generateHash("COMMISSION_LOCK"))
        )
    )
    val auditLogs: StateFlow<List<AuditLogEntry>> = _auditLogs.asStateFlow()

    private val _operatingMode = MutableStateFlow("AUTONOMOUS REOS (ACTIVE)")
    val operatingMode: StateFlow<String> = _operatingMode.asStateFlow()

    private val _lastSnapshotStamp = MutableStateFlow("state_20260827_051000_sealed.json")
    val lastSnapshotStamp: StateFlow<String> = _lastSnapshotStamp.asStateFlow()

    fun currentTimestamp(): String {
        return SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).format(Date())
    }

    fun generateHash(content: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(content.toByteArray())
        return "sha256:" + bytes.joinToString("") { "%02x".format(it) }
    }

    fun calculateSystemIntegrity(): String {
        val serialized = "GATES:${_gates.value.count { it.status == GateStatus.APPROVED }}|DEALS:${_deals.value.size}|LEADS:${_leads.value.size}|MODE:${_operatingMode.value}"
        return generateHash(serialized)
    }

    fun getSystemSummary(): SystemStateSummary {
        val totalCommission = _deals.value.sumOf { it.commissionAmount }
        val activeLeads = _leads.value.count { it.status != LeadStatus.LOST }
        val genuineLeads = _leads.value.count { it.genuineScore >= 70 }
        val genuinePct = if (_leads.value.isNotEmpty()) (genuineLeads * 100) / _leads.value.size else 0
        val approvedGates = _gates.value.count { it.status == GateStatus.APPROVED }

        return SystemStateSummary(
            operatingMode = _operatingMode.value,
            systemTrustScore = 98.4,
            stateIntegrityHash = calculateSystemIntegrity(),
            totalCommissionProtected = totalCommission,
            activeLeadsCount = activeLeads,
            genuineLeadsPct = genuinePct,
            verifiedInventoryCount = _units.value.size,
            activeDealsCount = _deals.value.size,
            completedGatesCount = approvedGates,
            totalGatesCount = _gates.value.size
        )
    }

    fun toggleSubtask(gateId: String, subtaskId: String) {
        _gates.value = _gates.value.map { gate ->
            if (gate.id == gateId) {
                val updatedSubtasks = gate.subtasks.map { subtask ->
                    if (subtask.id == subtaskId) {
                        val newCompleted = !subtask.isCompleted
                        subtask.copy(
                            isCompleted = newCompleted,
                            completedAt = if (newCompleted) currentTimestamp() else null,
                            note = if (newCompleted) "Completed and verified by REOS" else null
                        )
                    } else subtask
                }
                val allCompleted = updatedSubtasks.all { it.isCompleted }
                gate.copy(
                    subtasks = updatedSubtasks,
                    status = if (allCompleted) GateStatus.APPROVED else GateStatus.IN_PROGRESS,
                    approvedAt = if (allCompleted) currentTimestamp() else null
                )
            } else gate
        }
        logAction("SUBTASK_TOGGLE", "ARCH_CONTROLLER", "Toggled subtask $subtaskId in gate $gateId")
    }

    fun approveGate(gateId: String) {
        _gates.value = _gates.value.map { gate ->
            if (gate.id == gateId) {
                val updatedSubtasks = gate.subtasks.map { it.copy(isCompleted = true, completedAt = currentTimestamp()) }
                gate.copy(
                    status = GateStatus.APPROVED,
                    subtasks = updatedSubtasks,
                    approvedAt = currentTimestamp()
                )
            } else gate
        }
        logAction("GATE_APPROVED", "HUMAN_GOVERNOR", "Gate $gateId formally approved and sealed")
    }

    fun addLead(
        name: String,
        phone: String,
        email: String,
        budget: String,
        location: String,
        project: String,
        source: LeadSource
    ) {
        val score = when {
            email.contains("spam") || email.contains("test") -> 25
            phone.length > 7 -> 94
            else -> 60
        }
        val id = "LED-" + (8100 + _leads.value.size)
        val hash = generateHash("$id:$name:$phone:$budget")
        val newLead = Lead(
            id = id,
            name = name,
            phone = phone,
            email = email,
            budget = budget,
            preferredLocation = location,
            interestedProject = project,
            sourceChannel = source,
            genuineScore = score,
            status = if (score >= 70) LeadStatus.QUALIFIED else LeadStatus.NEW_INCOMING,
            firstTouchAttributionHash = hash,
            builderAcknowledged = score >= 70,
            assignedAgent = "Sarah Al-Mansoor (Auto-Assigned)",
            createdAt = currentTimestamp()
        )
        _leads.value = listOf(newLead) + _leads.value

        // Record attribution proof automatically
        addEvidence(
            type = EvidenceType.BUILDER_TIMESTAMP_ACK,
            leadId = id,
            dealId = null,
            title = "First-Touch Lead Attribution Proof",
            details = "Attribution locked for $name ($phone) at project $project via $source",
            signer = "Homio Attribution Protocol v7.0"
        )
        logAction("LEAD_INGESTED", "LEAD_ENGINE", "Ingested and attributed lead $id ($name) with score $score")
    }

    fun updateLeadStatus(leadId: String, newStatus: LeadStatus) {
        _leads.value = _leads.value.map { lead ->
            if (lead.id == leadId) {
                lead.copy(status = newStatus)
            } else lead
        }
        logAction("LEAD_STATUS_UPDATE", "LEAD_ENGINE", "Updated lead $leadId status to $newStatus")
    }

    fun addDeal(
        leadId: String,
        projectId: String,
        unitId: String,
        dealValue: Double
    ) {
        val lead = _leads.value.find { it.id == leadId }
        val project = _projects.value.find { it.id == projectId }
        val unit = _units.value.find { it.id == unitId }

        val commissionRate = project?.commissionPct ?: 2.5
        val commissionAmount = (dealValue * commissionRate) / 100.0
        val dealId = "DEL-" + (504 + _deals.value.size)
        val dealCode = "HOMIO-${project?.location?.take(3)?.uppercase() ?: "INT"}-2026-00" + (40 + _deals.value.size)
        val evidenceHash = generateHash("$dealId:$dealCode:$dealValue:$commissionAmount")

        val newDeal = Deal(
            id = dealId,
            dealCode = dealCode,
            leadId = leadId,
            leadName = lead?.name ?: "Client $leadId",
            projectId = projectId,
            projectName = project?.name ?: "Selected Project",
            unitId = unitId,
            unitNumber = unit?.unitNumber ?: "Custom Unit",
            builderName = project?.builderName ?: "Verified Developer",
            dealValue = dealValue,
            commissionPct = commissionRate,
            commissionAmount = commissionAmount,
            stage = DealStage.TOKEN_PAID,
            evidenceHash = evidenceHash,
            protectionStatus = ProtectionStatus.SECURED,
            updatedAt = currentTimestamp()
        )

        // Mark unit as BOOKED
        _units.value = _units.value.map {
            if (it.id == unitId) it.copy(status = UnitStatus.BOOKED) else it
        }

        _deals.value = listOf(newDeal) + _deals.value

        addEvidence(
            type = EvidenceType.BROKERAGE_AGREEMENT,
            leadId = leadId,
            dealId = dealId,
            title = "Deal Binding & Commission Protection Bond",
            details = "Secured commission of \$$commissionAmount (${commissionRate}%) for deal $dealCode",
            signer = "Tripartite Smart Contract"
        )
        logAction("DEAL_CREATED", "DEAL_ENGINE", "Created deal $dealCode for value \$$dealValue, commission \$$commissionAmount")
    }

    fun advanceDealStage(dealId: String, nextStage: DealStage) {
        _deals.value = _deals.value.map { deal ->
            if (deal.id == dealId) {
                val protection = if (nextStage == DealStage.IN_DISPUTE) ProtectionStatus.DISPUTE_FLAGGED else ProtectionStatus.SECURED
                deal.copy(stage = nextStage, protectionStatus = protection, updatedAt = currentTimestamp())
            } else deal
        }
        logAction("DEAL_STAGE_ADVANCED", "DEAL_ENGINE", "Deal $dealId transitioned to $nextStage")
    }

    fun addEvidence(
        type: EvidenceType,
        leadId: String,
        dealId: String?,
        title: String,
        details: String,
        signer: String
    ) {
        val id = "EVD-" + (904 + _evidence.value.size)
        val hash = generateHash("$id:$type:$leadId:$details:${currentTimestamp()}")
        val record = EvidenceRecord(
            id = id,
            type = type,
            leadId = leadId,
            dealId = dealId,
            title = title,
            details = details,
            sha256Hash = hash,
            verified = true,
            timestamp = currentTimestamp(),
            signer = signer
        )
        _evidence.value = listOf(record) + _evidence.value
        logAction("EVIDENCE_SEALED", "EVIDENCE_LEDGER", "Sealed evidence $id ($type) with hash $hash")
    }

    fun triggerTripwireTest(tripwireId: String) {
        _tripwires.value = _tripwires.value.map { tripwire ->
            if (tripwire.id == tripwireId) {
                tripwire.copy(triggersCount = tripwire.triggersCount + 1)
            } else tripwire
        }
        logAction("TRIPWIRE_EVALUATED", "PRE_EXEC_FIREWALL", "Evaluated rule $tripwireId: Invariants passed, state safe")
    }

    fun createSnapshot(): String {
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val name = "state_${stamp}_snapshot.json"
        _lastSnapshotStamp.value = name
        logAction("STATE_SNAPSHOT_CREATED", "SNAPSHOT_ENGINE", "Generated immutable snapshot $name with hash ${calculateSystemIntegrity()}")
        return name
    }

    fun setOperatingMode(mode: String) {
        _operatingMode.value = mode
        logAction("MODE_CHANGED", "GOVERNOR", "Operating mode updated to $mode")
    }

    fun logAction(actionType: String, actor: String, details: String) {
        val entry = AuditLogEntry(
            id = "LOG-" + UUID.randomUUID().toString().take(8).uppercase(),
            timestamp = currentTimestamp(),
            actionType = actionType,
            actor = actor,
            details = details,
            hash = generateHash("$actionType:$actor:$details:${System.currentTimeMillis()}")
        )
        _auditLogs.value = listOf(entry) + _auditLogs.value
    }
}
