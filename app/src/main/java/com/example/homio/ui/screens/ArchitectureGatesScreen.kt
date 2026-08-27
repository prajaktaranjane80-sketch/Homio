package com.example.homio.ui.screens

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.ArchitectureGate
import com.example.homio.model.GateStatus
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.GateStatusBadge
import com.example.homio.ui.components.SeverityBadge

@Composable
fun ArchitectureGatesScreen(
    viewModel: HomioViewModel
) {
    val gates = viewModel.gates.value
    var selectedFilter by remember { mutableStateOf("ALL") }
    var searchQuery by remember { mutableStateOf("") }
    var expandedGateId by remember { mutableStateOf<String?>("ARCH-039") }

    val filteredGates = gates.filter { gate ->
        val matchesPhase = when (selectedFilter) {
            "PHASE_1" -> gate.phase == "PHASE_1"
            "PHASE_2" -> gate.phase == "PHASE_2"
            "IN_PROGRESS" -> gate.status == GateStatus.IN_PROGRESS
            else -> true
        }
        val matchesSearch = gate.name.contains(searchQuery, ignoreCase = true) ||
                gate.id.contains(searchQuery, ignoreCase = true) ||
                gate.objective.contains(searchQuery, ignoreCase = true)
        matchesPhase && matchesSearch
    }

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
                    text = "Architecture Gates & State Machine",
                    style = MaterialTheme.typography.titleLarge,
                    color = TextPrimary
                )
                Text(
                    text = "Canonical governance sequence derived from data/state.json. Gates must satisfy all criteria before approval.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary,
                    fontSize = 12.sp
                )
            }
        }

        // Search Bar
        item {
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = { Text("Search 39 Architecture Gates...", color = TextMuted) },
                leadingIcon = { Icon(Icons.Default.Search, contentDescription = null, tint = CyanAccent) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary,
                    focusedBorderColor = CyanAccent,
                    unfocusedBorderColor = BorderSubtle
                ),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth()
            )
        }

        // Phase Filters
        item {
            LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                val filters = listOf(
                    "ALL" to "All Gates (${gates.size})",
                    "PHASE_1" to "Phase 1: Core Engines (20)",
                    "PHASE_2" to "Phase 2: Data & Infra (19)",
                    "IN_PROGRESS" to "Active / In-Progress"
                )
                items(filters) { (key, label) ->
                    val isSelected = selectedFilter == key
                    Box(
                        modifier = Modifier
                            .background(
                                if (isSelected) CyanAccent else SurfaceCard,
                                RoundedCornerShape(8.dp)
                            )
                            .border(
                                1.dp,
                                if (isSelected) CyanAccent else BorderSubtle,
                                RoundedCornerShape(8.dp)
                            )
                            .clickable { selectedFilter = key }
                            .padding(horizontal = 12.dp, vertical = 6.dp)
                    ) {
                        Text(
                            text = label,
                            color = if (isSelected) DarkNavy else TextSecondary,
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                        )
                    }
                }
            }
        }

        // Gates List
        items(filteredGates) { gate ->
            val isExpanded = expandedGateId == gate.id
            GateCard(
                gate = gate,
                isExpanded = isExpanded,
                onToggleExpand = {
                    expandedGateId = if (isExpanded) null else gate.id
                },
                onToggleSubtask = { subtaskId ->
                    viewModel.toggleSubtask(gate.id, subtaskId)
                },
                onApproveGate = {
                    viewModel.approveGate(gate.id)
                }
            )
        }
    }
}

@Composable
fun GateCard(
    gate: ArchitectureGate,
    isExpanded: Boolean,
    onToggleExpand: () -> Unit,
    onToggleSubtask: (String) -> Unit,
    onApproveGate: () -> Unit
) {
    val completedSubtasks = gate.subtasks.count { it.isCompleted }
    val totalSubtasks = gate.subtasks.size

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(SurfaceCard, RoundedCornerShape(12.dp))
            .border(
                1.dp,
                if (gate.status == GateStatus.IN_PROGRESS) CyanAccent else BorderSubtle,
                RoundedCornerShape(12.dp)
            )
            .padding(14.dp)
    ) {
        Column {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onToggleExpand() },
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = gate.id,
                            color = CyanAccent,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        GateStatusBadge(status = gate.status)
                    }

                    Spacer(modifier = Modifier.height(4.dp))

                    Text(
                        text = gate.name,
                        color = TextPrimary,
                        style = MaterialTheme.typography.titleMedium,
                        fontSize = 15.sp
                    )
                }

                Icon(
                    imageVector = if (isExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = null,
                    tint = TextSecondary
                )
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = gate.objective,
                color = TextSecondary,
                style = MaterialTheme.typography.bodyMedium,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            if (totalSubtasks > 0) {
                Spacer(modifier = Modifier.height(8.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Subtasks: $completedSubtasks / $totalSubtasks Completed",
                        color = if (completedSubtasks == totalSubtasks) EmeraldSuccess else GoldAccentLight,
                        style = MaterialTheme.typography.labelSmall,
                        fontSize = 10.sp
                    )
                    LinearProgressIndicator(
                        progress = { if (totalSubtasks > 0) completedSubtasks.toFloat() / totalSubtasks.toFloat() else 0f },
                        modifier = Modifier
                            .width(100.dp)
                            .height(6.dp),
                        color = if (completedSubtasks == totalSubtasks) EmeraldSuccess else CyanAccent,
                        trackColor = DarkNavy
                    )
                }
            }

            AnimatedVisibility(visible = isExpanded) {
                Column(modifier = Modifier.padding(top = 12.dp)) {
                    Divider(color = BorderSubtle, thickness = 1.dp)
                    Spacer(modifier = Modifier.height(10.dp))

                    Text(
                        text = "AUTHORITATIVE SUBTASKS",
                        color = CyanAccent,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    gate.subtasks.forEach { subtask ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Checkbox(
                                checked = subtask.isCompleted,
                                onCheckedChange = { onToggleSubtask(subtask.id) },
                                colors = CheckboxDefaults.colors(
                                    checkedColor = CyanAccent,
                                    checkmarkColor = DarkNavy,
                                    uncheckedColor = TextSecondary
                                )
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        text = "${subtask.id}: ${subtask.title}",
                                        color = if (subtask.isCompleted) TextPrimary else TextSecondary,
                                        style = MaterialTheme.typography.bodyMedium,
                                        fontSize = 12.sp
                                    )
                                    Spacer(modifier = Modifier.width(6.dp))
                                    SeverityBadge(severity = subtask.severity)
                                }
                                subtask.note?.let {
                                    Text(
                                        text = it,
                                        color = EmeraldSuccess,
                                        style = MaterialTheme.typography.bodySmall,
                                        fontSize = 10.sp
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "ACCEPTANCE CRITERIA",
                        color = GoldAccentLight,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    gate.criteria.forEach { crit ->
                        Row(
                            modifier = Modifier.padding(vertical = 2.dp),
                            verticalAlignment = Alignment.Top
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = EmeraldSuccess,
                                modifier = Modifier
                                    .size(14.dp)
                                    .padding(top = 2.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = crit,
                                color = TextSecondary,
                                style = MaterialTheme.typography.bodyMedium,
                                fontSize = 11.sp
                            )
                        }
                    }

                    if (gate.status != GateStatus.APPROVED) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(
                            onClick = onApproveGate,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = CyanAccent,
                                contentColor = DarkNavy
                            ),
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Lock, contentDescription = null, modifier = Modifier.size(16.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Approve & Seal ${gate.id}",
                                style = MaterialTheme.typography.labelLarge
                            )
                        }
                    }
                }
            }
        }
    }
}
