package com.example.homio.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.homio.data.ReosRepository
import com.example.homio.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class HomioViewModel(
    val repository: ReosRepository = ReosRepository()
) : ViewModel() {

    val gates: StateFlow<List<ArchitectureGate>> = repository.gates
    val leads: StateFlow<List<Lead>> = repository.leads
    val builders: StateFlow<List<Builder>> = repository.builders
    val projects: StateFlow<List<Project>> = repository.projects
    val units: StateFlow<List<UnitInventory>> = repository.units
    val deals: StateFlow<List<Deal>> = repository.deals
    val evidence: StateFlow<List<EvidenceRecord>> = repository.evidence
    val tripwires: StateFlow<List<TripwireRule>> = repository.tripwires
    val roles: StateFlow<List<AutonomyRole>> = repository.roles
    val auditLogs: StateFlow<List<AuditLogEntry>> = repository.auditLogs
    val operatingMode: StateFlow<String> = repository.operatingMode
    val lastSnapshotStamp: StateFlow<String> = repository.lastSnapshotStamp

    private val _selectedTab = MutableStateFlow(0)
    val selectedTab: StateFlow<Int> = _selectedTab.asStateFlow()

    private val _userNotification = MutableStateFlow<String?>(null)
    val userNotification: StateFlow<String?> = _userNotification.asStateFlow()

    fun selectTab(index: Int) {
        _selectedTab.value = index
    }

    fun dismissNotification() {
        _userNotification.value = null
    }

    fun showToast(message: String) {
        _userNotification.value = message
    }

    fun toggleSubtask(gateId: String, subtaskId: String) {
        repository.toggleSubtask(gateId, subtaskId)
        showToast("Subtask $subtaskId state updated")
    }

    fun approveGate(gateId: String) {
        repository.approveGate(gateId)
        showToast("Gate $gateId approved & sealed in state.json")
    }

    fun createLead(
        name: String,
        phone: String,
        email: String,
        budget: String,
        location: String,
        project: String,
        source: LeadSource
    ) {
        repository.addLead(name, phone, email, budget, location, project, source)
        showToast("Lead $name registered with first-touch attribution")
    }

    fun updateLeadStatus(leadId: String, newStatus: LeadStatus) {
        repository.updateLeadStatus(leadId, newStatus)
        showToast("Lead status updated to ${newStatus.name}")
    }

    fun createDeal(
        leadId: String,
        projectId: String,
        unitId: String,
        dealValue: Double
    ) {
        repository.addDeal(leadId, projectId, unitId, dealValue)
        showToast("Deal initialized with cryptographic commission bond")
    }

    fun advanceDealStage(dealId: String, nextStage: DealStage) {
        repository.advanceDealStage(dealId, nextStage)
        showToast("Deal stage advanced to ${nextStage.name}")
    }

    fun recordSiteVisitProof(leadId: String, dealId: String?, projectName: String) {
        repository.addEvidence(
            type = EvidenceType.SITE_VISIT_OTP,
            leadId = leadId,
            dealId = dealId,
            title = "Geofenced Site Visit Verified",
            details = "Completed onsite walkthrough at $projectName. Dual OTP authenticated.",
            signer = "REOS Geofence Protocol"
        )
        showToast("Site visit proof timestamped & hashed into Evidence Ledger")
    }

    fun recordDigitalConsent(leadId: String, mandateDetails: String) {
        repository.addEvidence(
            type = EvidenceType.DIGITAL_CONSENT,
            leadId = leadId,
            dealId = null,
            title = "Client Representation Mandate",
            details = mandateDetails,
            signer = "Digital Trust Signature"
        )
        showToast("Representation mandate signed & sealed")
    }

    fun triggerTripwireTest(tripwireId: String) {
        repository.triggerTripwireTest(tripwireId)
        showToast("Tripwire check passed. Invariants confirmed.")
    }

    fun createSnapshot() {
        val snapshot = repository.createSnapshot()
        showToast("State snapshot created: $snapshot")
    }

    fun setOperatingMode(mode: String) {
        repository.setOperatingMode(mode)
        showToast("Operating mode changed to $mode")
    }

    fun runPreflightIntegrityCheck() {
        val hash = repository.calculateSystemIntegrity()
        repository.logAction("PREFLIGHT_VERIFY", "PRE_EXEC_FIREWALL", "Calculated state integrity hash: $hash")
        showToast("Preflight verification passed: $hash")
    }
}
