package com.example.homio.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import com.example.homio.model.*
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.AddDealDialog
import com.example.homio.ui.components.HashBadge
import com.example.homio.ui.components.ProtectionBadge

@Composable
fun InventoryDealsScreen(
    viewModel: HomioViewModel
) {
    val builders = viewModel.builders.value
    val projects = viewModel.projects.value
    val units = viewModel.units.value
    val deals = viewModel.deals.value
    val leads = viewModel.leads.value

    var selectedSection by remember { mutableStateOf("DEALS") }
    var showAddDealDialog by remember { mutableStateOf(false) }

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
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "Inventory & Commission Deals",
                        style = MaterialTheme.typography.titleLarge,
                        color = TextPrimary
                    )
                    Text(
                        text = "Builder acquisition, live unit status & immutable commission protection",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextSecondary,
                        fontSize = 12.sp
                    )
                }

                Button(
                    onClick = { showAddDealDialog = true },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = GoldAccent,
                        contentColor = DarkNavy
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(16.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("New Deal", style = MaterialTheme.typography.labelLarge)
                }
            }
        }

        // Section Tabs
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(
                    "DEALS" to "Active Deals (${deals.size})",
                    "INVENTORY" to "Unit Inventory (${units.size})",
                    "BUILDERS" to "Verified Builders (${builders.size})"
                ).forEach { (key, label) ->
                    val isSelected = selectedSection == key
                    Box(
                        modifier = Modifier
                            .weight(1f)
                            .background(
                                if (isSelected) SurfaceCardElevated else SurfaceCard,
                                RoundedCornerShape(8.dp)
                            )
                            .border(
                                1.dp,
                                if (isSelected) GoldAccent else BorderSubtle,
                                RoundedCornerShape(8.dp)
                            )
                            .clickable { selectedSection = key }
                            .padding(vertical = 8.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = label,
                            color = if (isSelected) GoldAccentLight else TextSecondary,
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                            fontSize = 10.sp
                        )
                    }
                }
            }
        }

        when (selectedSection) {
            "DEALS" -> {
                items(deals) { deal ->
                    DealCard(
                        deal = deal,
                        onAdvanceStage = { nextStage ->
                            viewModel.advanceDealStage(deal.id, nextStage)
                        }
                    )
                }
            }
            "INVENTORY" -> {
                items(units) { unit ->
                    UnitCard(unit = unit)
                }
            }
            "BUILDERS" -> {
                items(builders) { builder ->
                    BuilderCard(builder = builder)
                }
            }
        }
    }

    if (showAddDealDialog) {
        AddDealDialog(
            leads = leads,
            projects = projects,
            units = units,
            onDismiss = { showAddDealDialog = false },
            onConfirm = { leadId, projectId, unitId, dealValue ->
                viewModel.createDeal(leadId, projectId, unitId, dealValue)
                showAddDealDialog = false
            }
        )
    }
}

@Composable
fun DealCard(
    deal: Deal,
    onAdvanceStage: (DealStage) -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(12.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(12.dp))
            .padding(14.dp)
    ) {
        Column {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = deal.dealCode,
                        color = CyanAccent,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                    Text(
                        text = "${deal.projectName} • ${deal.unitNumber}",
                        color = TextPrimary,
                        style = MaterialTheme.typography.bodyMedium,
                        fontSize = 13.sp
                    )
                }
                ProtectionBadge(status = deal.protectionStatus)
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Deal Economics Box
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(DarkNavy, RoundedCornerShape(8.dp))
                    .padding(10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text("Client Name", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                        Text(deal.leadName, color = TextPrimary, style = MaterialTheme.typography.bodyMedium)
                    }
                    Column {
                        Text("Agreed Deal Value", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                        Text(
                            "$${deal.dealValue.toInt().toString().reversed().chunked(3).joinToString(",").reversed()}",
                            color = TextPrimary,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                    Column(horizontalAlignment = Alignment.End) {
                        Text("Protected Commission", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                        Text(
                            "$${deal.commissionAmount.toInt().toString().reversed().chunked(3).joinToString(",").reversed()}",
                            color = GoldAccentLight,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Stage and Evidence Hash
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Stage: ", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                    Text(deal.stage.name.replace("_", " "), color = EmeraldSuccess, style = MaterialTheme.typography.labelMedium)
                }
                HashBadge(hash = deal.evidenceHash)
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Advance Stage Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                if (deal.stage == DealStage.TOKEN_PAID) {
                    Button(
                        onClick = { onAdvanceStage(DealStage.AGREEMENT_SIGNED) },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = CyanAccent, contentColor = DarkNavy),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("Sign Agreement", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                    }
                }

                if (deal.stage == DealStage.AGREEMENT_SIGNED) {
                    Button(
                        onClick = { onAdvanceStage(DealStage.COMMISSION_INVOICED) },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = GoldAccent, contentColor = DarkNavy),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("Invoice Builder", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                    }
                }

                if (deal.stage == DealStage.COMMISSION_INVOICED) {
                    Button(
                        onClick = { onAdvanceStage(DealStage.COMMISSION_DISBURSED) },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = EmeraldSuccess, contentColor = DarkNavy),
                        shape = RoundedCornerShape(6.dp)
                    ) {
                        Text("Disburse Escrow", style = MaterialTheme.typography.labelSmall, fontSize = 10.sp)
                    }
                }
            }
        }
    }
}

@Composable
fun UnitCard(unit: UnitInventory) {
    val statusColor = when (unit.status) {
        UnitStatus.AVAILABLE -> EmeraldSuccess
        UnitStatus.BLOCKED -> GoldAccent
        UnitStatus.BOOKED -> CyanAccent
        UnitStatus.SOLD -> RoseAlert
    }

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
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(unit.unitNumber, color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(unit.tower, color = TextSecondary, style = MaterialTheme.typography.bodySmall)
                }
                Text("${unit.projectName} • ${unit.type}", color = TextSecondary, style = MaterialTheme.typography.bodyMedium)
                Text("${unit.carpetAreaSqFt} sq.ft. carpet", color = TextMuted, style = MaterialTheme.typography.bodySmall)
            }

            Column(horizontalAlignment = Alignment.End) {
                Text(
                    "$${unit.price.toInt().toString().reversed().chunked(3).joinToString(",").reversed()}",
                    color = TextPrimary,
                    style = MaterialTheme.typography.titleMedium
                )
                Text(
                    "Comm: $${unit.commissionAmount.toInt()}",
                    color = GoldAccentLight,
                    style = MaterialTheme.typography.labelSmall
                )
                Spacer(modifier = Modifier.height(4.dp))
                Box(
                    modifier = Modifier
                        .background(statusColor.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                        .padding(horizontal = 6.dp, vertical = 2.dp)
                ) {
                    Text(unit.status.name, color = statusColor, style = MaterialTheme.typography.labelSmall, fontSize = 9.sp)
                }
            }
        }
    }
}

@Composable
fun BuilderCard(builder: Builder) {
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
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(builder.name, color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.width(6.dp))
                    Box(
                        modifier = Modifier
                            .background(CyanAccent.copy(alpha = 0.15f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 5.dp, vertical = 2.dp)
                    ) {
                        Text(builder.tier.replace("_", " "), color = CyanAccent, style = MaterialTheme.typography.labelSmall, fontSize = 9.sp)
                    }
                }
                Text("${builder.city} • ${builder.activeProjects} Live Projects", color = TextSecondary, style = MaterialTheme.typography.bodyMedium)
                Text("Standard Broker Commission: ${builder.standardCommissionPct}%", color = GoldAccentLight, style = MaterialTheme.typography.bodySmall)
            }

            Column(horizontalAlignment = Alignment.End) {
                Text("Trust Score", color = TextMuted, style = MaterialTheme.typography.labelSmall)
                Text("${builder.trustScore}%", color = EmeraldSuccess, style = MaterialTheme.typography.titleLarge)
                Text(if (builder.disputeCount == 0) "0 Disputes" else "${builder.disputeCount} Disputes", color = if (builder.disputeCount == 0) EmeraldSuccess else RoseAlert, style = MaterialTheme.typography.labelSmall)
            }
        }
    }
}
