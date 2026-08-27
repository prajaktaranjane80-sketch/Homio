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
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.Lead
import com.example.homio.model.LeadSource
import com.example.homio.model.LeadStatus
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.AddLeadDialog
import com.example.homio.ui.components.HashBadge

@Composable
fun LeadEngineScreen(
    viewModel: HomioViewModel
) {
    val leads = viewModel.leads.value
    val projects = viewModel.projects.value
    var showAddLeadDialog by remember { mutableStateOf(false) }
    var selectedLeadForDetails by remember { mutableStateOf<Lead?>(null) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkNavy)
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 80.dp)
    ) {
        // Screen Header & Lead Counter
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Lead Engine & Attribution",
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary
                    )
                    Text(
                        text = "Real-time qualification, genuine buyer scoring & first-touch protection",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary,
                        fontSize = 12.sp
                    )
                }

                Button(
                    onClick = { showAddLeadDialog = true },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = CyanAccent,
                        contentColor = DarkNavy
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Add Lead", style = MaterialTheme.typography.labelLarge)
                }
            }
        }

        // Summary Bar: Genuine vs Suspicious
        item {
            val genuineCount = leads.count { it.genuineScore >= 70 }
            val suspiciousCount = leads.count { it.genuineScore < 70 }
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(SurfaceCard, RoundedCornerShape(10.dp))
                    .border(1.dp, BorderSubtle, RoundedCornerShape(10.dp))
                    .padding(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceAround,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Genuine Qualified", color = EmeraldSuccess, style = MaterialTheme.typography.labelSmall)
                        Text("$genuineCount Leads", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                    }
                    Divider(
                        modifier = Modifier
                            .height(28.dp)
                            .width(1.dp),
                        color = BorderSubtle
                    )
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Flagged / Spam", color = RoseAlert, style = MaterialTheme.typography.labelSmall)
                        Text("$suspiciousCount Isolated", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                    }
                    Divider(
                        modifier = Modifier
                            .height(28.dp)
                            .width(1.dp),
                        color = BorderSubtle
                    )
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("Attribution Lock", color = CyanAccent, style = MaterialTheme.typography.labelSmall)
                        Text("100% SHA-256", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                    }
                }
            }
        }

        // Lead Cards
        items(leads) { lead ->
            LeadCard(
                lead = lead,
                onStatusChange = { newStatus ->
                    viewModel.updateLeadStatus(lead.id, newStatus)
                },
                onGenerateProof = {
                    viewModel.recordSiteVisitProof(lead.id, null, lead.interestedProject)
                }
            )
        }
    }

    if (showAddLeadDialog) {
        AddLeadDialog(
            projects = projects,
            onDismiss = { showAddLeadDialog = false },
            onConfirm = { name, phone, email, budget, location, project, source ->
                viewModel.createLead(name, phone, email, budget, location, project, source)
                showAddLeadDialog = false
            }
        )
    }
}

@Composable
fun LeadCard(
    lead: Lead,
    onStatusChange: (LeadStatus) -> Unit,
    onGenerateProof: () -> Unit
) {
    val scoreColor = when {
        lead.genuineScore >= 90 -> EmeraldSuccess
        lead.genuineScore >= 70 -> CyanAccent
        lead.genuineScore >= 50 -> GoldAccent
        else -> RoseAlert
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(12.dp))
            .border(
                1.dp,
                if (lead.genuineScore >= 70) BorderSubtle else RoseAlert.copy(alpha = 0.5f),
                RoundedCornerShape(12.dp)
            )
            .padding(14.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = lead.name,
                            color = TextPrimary,
                            style = MaterialTheme.typography.titleMedium,
                            fontSize = 15.sp
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "(${lead.id})",
                            color = TextMuted,
                            style = MaterialTheme.typography.bodySmall,
                            fontSize = 11.sp
                        )
                    }
                    Text(
                        text = "${lead.phone} • ${lead.email}",
                        color = TextSecondary,
                        style = MaterialTheme.typography.bodySmall,
                        fontSize = 11.sp
                    )
                }

                // Genuine Score Pill
                Box(
                    modifier = Modifier
                        .background(scoreColor.copy(alpha = 0.15f), RoundedCornerShape(8.dp))
                        .border(1.dp, scoreColor.copy(alpha = 0.4f), RoundedCornerShape(8.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            text = "${lead.genuineScore}",
                            color = scoreColor,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                        Text(
                            text = "GENUINE",
                            color = scoreColor,
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = 8.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Details Row
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(DarkNavy, RoundedCornerShape(8.dp))
                    .padding(8.dp),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Budget Slab", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                    Text(lead.budget, color = TextPrimary, style = MaterialTheme.typography.bodyMedium, fontSize = 12.sp)
                }
                Column {
                    Text("Interested Project", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                    Text(lead.interestedProject, color = CyanAccent, style = MaterialTheme.typography.bodyMedium, fontSize = 12.sp)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Source", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                    Text(lead.sourceChannel.name.replace("_", " "), color = GoldAccentLight, style = MaterialTheme.typography.bodyMedium, fontSize = 11.sp)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Attribution Fingerprint
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = if (lead.builderAcknowledged) Icons.Default.CheckCircle else Icons.Default.Warning,
                        contentDescription = null,
                        tint = if (lead.builderAcknowledged) EmeraldSuccess else GoldAccent,
                        modifier = Modifier.size(14.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = if (lead.builderAcknowledged) "Builder Acknowledged" else "Pending Builder Sync",
                        color = if (lead.builderAcknowledged) EmeraldSuccess else GoldAccent,
                        style = MaterialTheme.typography.labelSmall,
                        fontSize = 10.sp
                    )
                }

                HashBadge(hash = lead.firstTouchAttributionHash)
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Quick Status Actions Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedButton(
                    onClick = { onStatusChange(LeadStatus.VISIT_SCHEDULED) },
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(6.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = CyanAccent),
                    border = ButtonDefaults.outlinedButtonBorder.copy(brush = androidx.compose.ui.graphics.SolidColor(BorderSubtle))
                ) {
                    Text("Schedule Visit", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                }

                Button(
                    onClick = onGenerateProof,
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(6.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = SurfaceCardElevated, contentColor = EmeraldSuccess)
                ) {
                    Icon(Icons.Default.Verified, contentDescription = null, modifier = Modifier.size(12.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Verify Onsite OTP", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                }
            }
        }
    }
}
