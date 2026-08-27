package com.example.homio.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.AutonomyRole
import com.example.homio.model.EvidenceRecord
import com.example.homio.model.TripwireRule
import com.example.homio.model.TripwireSeverity
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.HashBadge

@Composable
fun EvidenceSecurityScreen(
    viewModel: HomioViewModel
) {
    val evidence = viewModel.evidence.value
    val tripwires = viewModel.tripwires.value
    val roles = viewModel.roles.value
    val lastSnapshot = viewModel.lastSnapshotStamp.value

    var selectedTab by remember { mutableStateOf("EVIDENCE") }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkNavy)
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 80.dp)
    ) {
        // Header
        item {
            Column {
                Text(
                    text = "Evidence Ledger & Security Firewall",
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary
                )
                Text(
                    text = "Immutable SHA-256 evidence records, active tripwire circuit breakers, and autonomous agent roles",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary,
                    fontSize = 12.sp
                )
            }
        }

        // Section Tabs
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(
                    "EVIDENCE" to "Evidence Ledger (${evidence.size})",
                    "TRIPWIRES" to "Tripwires & Firewall (${tripwires.size})",
                    "ROLES" to "Agent Roles (${roles.size})"
                ).forEach { (key, label) ->
                    val isSelected = selectedTab == key
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .background(
                                if (isSelected) SurfaceCardElevated else SurfaceCard,
                                RoundedCornerShape(8.dp)
                            )
                            .border(
                                1.dp,
                                if (isSelected) CyanAccent else BorderSubtle,
                                RoundedCornerShape(8.dp)
                            )
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        TextButton(
                            onClick = { selectedTab = key },
                            contentPadding = PaddingValues(0.dp)
                        ) {
                            Text(
                                text = label,
                                color = if (isSelected) CyanAccent else TextSecondary,
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 10.sp
                            )
                        }
                    }
                }
            }
        }

        when (selectedTab) {
            "EVIDENCE" -> {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(SurfaceCard, RoundedCornerShape(10.dp))
                            .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
                            .padding(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("Evidence Integrity", color = EmeraldSuccess, style = MaterialTheme.typography.labelSmall)
                                Text("100% Tamper-Proof Cryptographic Chain", color = TextPrimary, style = MaterialTheme.typography.bodyMedium)
                            }
                            Icon(Icons.Default.VerifiedUser, contentDescription = null, tint = EmeraldSuccess)
                        }
                    }
                }

                items(evidence) { record ->
                    EvidenceCard(record = record)
                }
            }

            "TRIPWIRES" -> {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(SurfaceCard, RoundedCornerShape(10.dp))
                            .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
                            .padding(12.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("Pre-Execution Firewall Status", color = RoseAlert, style = MaterialTheme.typography.labelSmall)
                                Text("Zero Unauthorized Mutation Allowed", color = TextPrimary, style = MaterialTheme.typography.bodyMedium)
                                Text("Latest Snapshot: $lastSnapshot", color = TextSecondary, style = MaterialTheme.typography.bodySmall, fontSize = 10.sp)
                            }
                            Button(
                                onClick = { viewModel.createSnapshot() },
                                colors = ButtonDefaults.buttonColors(containerColor = CyanAccent, contentColor = DarkNavy),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text("Snapshot Now", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                            }
                        }
                    }
                }

                items(tripwires) { tripwire ->
                    TripwireCard(
                        tripwire = tripwire,
                        onTriggerTest = { viewModel.triggerTripwireTest(tripwire.id) }
                    )
                }
            }

            "ROLES" -> {
                items(roles) { role ->
                    RoleCard(role = role)
                }
            }
        }
    }
}

@Composable
fun EvidenceCard(record: EvidenceRecord) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(10.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
            .padding(12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = EmeraldSuccess,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(record.title, color = TextPrimary, style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                }

                Box(
                    modifier = Modifier
                        .background(DarkNavy, RoundedCornerShape(4.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(record.type.name.replace("_", " "), color = CyanAccent, style = MaterialTheme.typography.labelSmall, fontSize = 9.sp)
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(record.details, color = TextSecondary, style = MaterialTheme.typography.bodyMedium, fontSize = 12.sp)

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Signer: ${record.signer}", color = GoldAccentLight, style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                HashBadge(hash = record.sha256Hash)
            }
        }
    }
}

@Composable
fun TripwireCard(
    tripwire: TripwireRule,
    onTriggerTest: () -> Unit
) {
    val severityColor = when (tripwire.severity) {
        TripwireSeverity.CRITICAL -> RoseAlert
        TripwireSeverity.HIGH -> GoldAccent
        TripwireSeverity.MONITORING -> BlueAccent
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(10.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
            .padding(12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(if (tripwire.isActive) EmeraldSuccess else RoseAlert, CircleShape)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(tripwire.name, color = TextPrimary, style = MaterialTheme.typography.titleMedium, fontSize = 14.sp)
                }

                Box(
                    modifier = Modifier
                        .background(severityColor.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(tripwire.severity.name, color = severityColor, style = MaterialTheme.typography.labelSmall, fontSize = 9.sp)
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(tripwire.description, color = TextSecondary, style = MaterialTheme.typography.bodyMedium, fontSize = 12.sp)

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    "Evaluations: ${tripwire.triggersCount} | Circuit: ARMED",
                    color = EmeraldSuccess,
                    style = MaterialTheme.typography.labelSmall,
                    fontSize = 10.sp
                )

                OutlinedButton(
                    onClick = onTriggerTest,
                    shape = RoundedCornerShape(6.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = CyanAccent),
                    border = ButtonDefaults.outlinedButtonBorder.copy(brush = androidx.compose.ui.graphics.SolidColor(BorderSubtle)),
                    contentPadding = PaddingValues(horizontal = 8.dp, vertical = 2.dp)
                ) {
                    Text("Evaluate Invariant", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                }
            }
        }
    }
}

@Composable
fun RoleCard(role: AutonomyRole) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(10.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
            .padding(12.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(role.name, color = CyanAccent, style = MaterialTheme.typography.titleMedium)
                    Text(role.title, color = TextSecondary, style = MaterialTheme.typography.bodySmall)
                }
                Box(
                    modifier = Modifier
                        .background(GoldAccent.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text("${role.activeTasks} Active Tasks", color = GoldAccentLight, style = MaterialTheme.typography.labelSmall, fontSize = 9.sp)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Text("Core Responsibilities:", color = TextMuted, style = MaterialTheme.typography.labelSmall)
            role.responsibilities.forEach { resp ->
                Row(modifier = Modifier.padding(vertical = 1.dp), verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(4.dp).background(CyanAccent, CircleShape))
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(resp, color = TextSecondary, style = MaterialTheme.typography.bodyMedium, fontSize = 12.sp)
                }
            }
        }
    }
}
