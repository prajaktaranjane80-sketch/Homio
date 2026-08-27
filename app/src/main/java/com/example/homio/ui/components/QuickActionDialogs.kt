package com.example.homio.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.Builder
import com.example.homio.model.Lead
import com.example.homio.model.LeadSource
import com.example.homio.model.Project
import com.example.homio.model.UnitInventory
import com.example.homio.theme.*

@Composable
fun AddLeadDialog(
    projects: List<Project>,
    onDismiss: () -> Unit,
    onConfirm: (name: String, phone: String, email: String, budget: String, location: String, project: String, source: LeadSource) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var budget by remember { mutableStateOf("$1.5M - $2.5M") }
    var location by remember { mutableStateOf("Dubai Marina") }
    var selectedProject by remember { mutableStateOf(projects.firstOrNull()?.name ?: "Emaar Beachfront") }
    var selectedSource by remember { mutableStateOf(LeadSource.AI_CONVERSATIONAL) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = SurfaceNavy,
        title = {
            Text("Register New Lead", color = TextPrimary, style = MaterialTheme.typography.titleLarge)
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Text(
                    "Lead will be cryptographically attributed with first-touch SHA-256 fingerprint.",
                    color = TextSecondary,
                    style = MaterialTheme.typography.bodyMedium
                )

                OutlinedTextField(
                    value = name,
                    onValueChange = { name = it },
                    label = { Text("Lead Full Name") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = phone,
                    onValueChange = { phone = it },
                    label = { Text("Phone (+Country Code)") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = email,
                    onValueChange = { email = it },
                    label = { Text("Email Address") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = budget,
                    onValueChange = { budget = it },
                    label = { Text("Budget Slab") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = location,
                    onValueChange = { location = it },
                    label = { Text("Preferred Micro-market") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = CyanAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (name.isNotBlank() && phone.isNotBlank()) {
                        onConfirm(name, phone, email, budget, location, selectedProject, selectedSource)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = CyanAccent, contentColor = DarkNavy)
            ) {
                Text("Attribute & Save Lead", style = MaterialTheme.typography.labelLarge)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TextSecondary)
            }
        }
    )
}

@Composable
fun AddDealDialog(
    leads: List<Lead>,
    projects: List<Project>,
    units: List<UnitInventory>,
    onDismiss: () -> Unit,
    onConfirm: (leadId: String, projectId: String, unitId: String, dealValue: Double) -> Unit
) {
    val qualifiedLeads = leads.filter { it.genuineScore >= 70 }
    var selectedLeadId by remember { mutableStateOf(qualifiedLeads.firstOrNull()?.id ?: "") }
    var selectedProjectId by remember { mutableStateOf(projects.firstOrNull()?.id ?: "") }
    var selectedUnitId by remember { mutableStateOf(units.firstOrNull()?.id ?: "") }
    var dealValueText by remember { mutableStateOf(units.firstOrNull()?.price?.toString() ?: "1450000") }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = SurfaceNavy,
        title = {
            Text("Initialize Deal & Commission Bond", color = TextPrimary, style = MaterialTheme.typography.titleLarge)
        },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Text(
                    "Binds Buyer, Project, Unit, and Broker Commission into an immutable tripartite contract.",
                    color = TextSecondary,
                    style = MaterialTheme.typography.bodyMedium
                )

                Text("Select Client:", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                qualifiedLeads.forEach { lead ->
                    val isSelected = lead.id == selectedLeadId
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (isSelected) SurfaceCardElevated else SurfaceCard, RoundedCornerShape(8.dp))
                            .border(1.dp, if (isSelected) CyanAccent else BorderSubtle, RoundedCornerShape(8.dp))
                            .clickable { selectedLeadId = lead.id }
                            .padding(10.dp)
                    ) {
                        Column {
                            Text("${lead.name} (${lead.id})", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                            Text("Score: ${lead.genuineScore} | Budget: ${lead.budget}", color = TextSecondary, style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text("Select Unit:", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                units.take(3).forEach { unit ->
                    val isSelected = unit.id == selectedUnitId
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(if (isSelected) SurfaceCardElevated else SurfaceCard, RoundedCornerShape(8.dp))
                            .border(1.dp, if (isSelected) GoldAccent else BorderSubtle, RoundedCornerShape(8.dp))
                            .clickable {
                                selectedUnitId = unit.id
                                selectedProjectId = unit.projectId
                                dealValueText = unit.price.toString()
                            }
                            .padding(10.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("${unit.projectName} - ${unit.unitNumber}", color = TextPrimary, style = MaterialTheme.typography.titleMedium)
                                Text("${unit.type} | ${unit.carpetAreaSqFt} sqft", color = TextSecondary, style = MaterialTheme.typography.bodyMedium)
                            }
                            Text("\$${unit.price.toInt()}", color = GoldAccentLight, style = MaterialTheme.typography.titleMedium)
                        }
                    }
                }

                OutlinedTextField(
                    value = dealValueText,
                    onValueChange = { dealValueText = it },
                    label = { Text("Agreed Deal Value ($)") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedTextColor = TextPrimary,
                        unfocusedTextColor = TextPrimary,
                        focusedBorderColor = GoldAccent,
                        unfocusedBorderColor = BorderSubtle
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    val value = dealValueText.toDoubleOrNull() ?: 1000000.0
                    if (selectedLeadId.isNotBlank() && selectedUnitId.isNotBlank()) {
                        onConfirm(selectedLeadId, selectedProjectId, selectedUnitId, value)
                    }
                },
                colors = ButtonDefaults.buttonColors(containerColor = GoldAccent, contentColor = DarkNavy)
            ) {
                Text("Lock Deal & Protect Commission", style = MaterialTheme.typography.labelLarge)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = TextSecondary)
            }
        }
    )
}
