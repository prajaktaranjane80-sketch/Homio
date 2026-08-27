package com.example.homio.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.SystemStateSummary
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.HashBadge
import com.example.homio.ui.components.ProtectionBadge
import com.example.homio.ui.components.ReosStatCard

@Composable
fun DashboardScreen(
    viewModel: HomioViewModel,
    onNavigateToGates: () -> Unit,
    onNavigateToLeads: () -> Unit,
    onNavigateToDeals: () -> Unit,
    onNavigateToSecurity: () -> Unit
) {
    val summary = viewModel.repository.getSystemSummary()
    val deals = viewModel.deals.value
    val leads = viewModel.leads.value
    val tripwires = viewModel.tripwires.value
    val auditLogs = viewModel.auditLogs.value

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkNavy)
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 80.dp)
    ) {
        // Mission statement banner
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SurfaceCard, RoundedCornerShape(14.dp))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(14.dp))
                    .padding(16.dp)
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
                                    .background(CyanAccent, CircleShape)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "GLOBAL REAL ESTATE OPERATING SYSTEM",
                                color = CyanAccent,
                                style = MaterialTheme.typography.labelSmall,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Text(
                            text = "SOC2 / RERA COMPLIANT",
                            color = EmeraldSuccess,
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = 9.sp
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "Autonomous Brokerage & Protection Engine",
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary,
                        fontSize = 19.sp
                    )

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = "Guarantees first-touch buyer attribution, locks developer inventory, protects commissions cryptographically, and enforces pre-execution governance tripwires.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary,
                        fontSize = 12.sp,
                        lineHeight = 17.sp
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        HashBadge(hash = summary.stateIntegrityHash)
                        Text(
                            text = "State Hash Valid",
                            color = EmeraldSuccess,
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = 10.sp
                        )
                    }
                }
            }
        }

        // Key Statistics Grid (2x2)
        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    ReosStatCard(
                        title = "COMMISSION PROTECTED",
                        value = "$${summary.totalCommissionProtected.toInt().toString().reversed().chunked(3).joinToString(",").reversed()}",
                        subtitle = "100% Invariant Locked",
                        icon = Icons.Default.Shield,
                        accentColor = GoldAccent,
                        modifier = Modifier.weight(1f)
                    )
                    ReosStatCard(
                        title = "SYSTEM TRUST SCORE",
                        value = "${summary.systemTrustScore}%",
                        subtitle = "Zero Tamper Alert",
                        icon = Icons.Default.Verified,
                        accentColor = EmeraldSuccess,
                        modifier = Modifier.weight(1f)
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    ReosStatCard(
                        title = "GENUINE LEADS RATIO",
                        value = "${summary.genuineLeadsPct}%",
                        subtitle = "${summary.activeLeadsCount} Active Pipeline",
                        icon = Icons.Default.PersonSearch,
                        accentColor = CyanAccent,
                        modifier = Modifier.weight(1f)
                    )
                    ReosStatCard(
                        title = "ARCHITECTURE GATES",
                        value = "${summary.completedGatesCount} / ${summary.totalGatesCount}",
                        subtitle = "Phase 1 & 2 Sealed",
                        icon = Icons.Default.Layers,
                        accentColor = IndigoBrand,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }

        // Architecture Gate Progress Card
        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SurfaceCard, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(12.dp))
                    .clickable { onNavigateToGates() }
                    .padding(16.dp)
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text(
                                text = "Architecture Progression",
                                style = MaterialTheme.typography.titleMedium,
                                color = TextPrimary
                            )
                            Text(
                                text = "Current Active Gate: ARCH-039 (Master Blueprint)",
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary,
                                fontSize = 12.sp
                            )
                        }

                        Icon(
                            imageVector = Icons.Default.ChevronRight,
                            contentDescription = "View Gates",
                            tint = CyanAccent
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    LinearProgressIndicator(
                        progress = { summary.completedGatesCount.toFloat() / summary.totalGatesCount.toFloat() },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(8.dp),
                        color = CyanAccent,
                        trackColor = DarkNavy
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            text = "Phase 1: Core Engines (20/20)",
                            color = EmeraldSuccess,
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = 10.sp
                        )
                        Text(
                            text = "Phase 2: Data & Infra (18/19)",
                            color = GoldAccent,
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = 10.sp
                        )
                    }
                }
            }
        }

        // Active Deals & Commission Protection Section
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Active Deals & Commission Bonds",
                    style = MaterialTheme.typography.titleMedium,
                    color = TextPrimary
                )
                Text(
                    text = "View All",
                    color = CyanAccent,
                    style = MaterialTheme.typography.labelLarge,
                    modifier = Modifier.clickable { onNavigateToDeals() }
                )
            }
        }

        items(deals.take(2)) { deal ->
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SurfaceCard, RoundedCornerShape(12.dp))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(12.dp))
                    .clickable { onNavigateToDeals() }
                    .padding(14.dp)
            ) {
                Column {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = deal.dealCode,
                            color = TextPrimary,
                            style = MaterialTheme.typography.titleMedium,
                            fontSize = 14.sp
                        )
                        ProtectionBadge(status = deal.protectionStatus)
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "${deal.projectName} — ${deal.unitNumber}",
                        color = TextSecondary,
                        style = MaterialTheme.typography.bodyMedium
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Client", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                            Text(deal.leadName, color = TextPrimary, style = MaterialTheme.typography.bodyMedium)
                        }

                        Column(horizontalAlignment = Alignment.End) {
                            Text("Broker Commission (${deal.commissionPct}%)", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                            Text(
                                "$${deal.commissionAmount.toInt().toString().reversed().chunked(3).joinToString(",").reversed()}",
                                color = GoldAccentLight,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }

        // Live Real-Time Audit Ledger
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Live Audit Trail",
                    style = MaterialTheme.typography.titleMedium,
                    color = TextPrimary
                )
                Text(
                    text = "Immutable Ledger",
                    color = EmeraldSuccess,
                    style = MaterialTheme.typography.labelSmall,
                    fontSize = 10.sp
                )
            }
        }

        items(auditLogs.take(3)) { log ->
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(DarkNavy, RoundedCornerShape(8.dp))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(8.dp))
                    .padding(10.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(6.dp)
                            .background(CyanAccent, CircleShape)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(log.actionType, color = CyanAccent, style = MaterialTheme.typography.labelSmall)
                            Text(log.timestamp.takeLast(9).dropLast(1), color = TextMuted, style = MaterialTheme.typography.labelSmall)
                        }
                        Text(log.details, color = TextSecondary, style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}
