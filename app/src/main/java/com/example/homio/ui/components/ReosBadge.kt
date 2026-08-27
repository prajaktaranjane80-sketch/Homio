package com.example.homio.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.model.GateStatus
import com.example.homio.model.ProtectionStatus
import com.example.homio.model.SubtaskSeverity
import com.example.homio.theme.*

@Composable
fun GateStatusBadge(status: GateStatus) {
    val (bgColor, textColor, label) = when (status) {
        GateStatus.APPROVED -> Triple(EmeraldSuccess.copy(alpha = 0.15f), EmeraldSuccess, "APPROVED")
        GateStatus.IN_PROGRESS -> Triple(GoldAccent.copy(alpha = 0.15f), GoldAccent, "IN PROGRESS")
        GateStatus.PENDING -> Triple(BlueAccent.copy(alpha = 0.15f), BlueAccent, "PENDING")
        GateStatus.BLOCKED -> Triple(RoseAlert.copy(alpha = 0.15f), RoseAlert, "BLOCKED")
    }

    Box(
        modifier = Modifier
            .background(bgColor, RoundedCornerShape(6.dp))
            .border(1.dp, textColor.copy(alpha = 0.4f), RoundedCornerShape(6.dp))
            .padding(horizontal = 8.dp, vertical = 3.dp)
    ) {
        Text(
            text = label,
            color = textColor,
            style = MaterialTheme.typography.labelSmall,
            fontSize = 10.sp
        )
    }
}

@Composable
fun SeverityBadge(severity: SubtaskSeverity) {
    val (color, label) = when (severity) {
        SubtaskSeverity.CRITICAL -> Pair(RoseAlert, "CRITICAL")
        SubtaskSeverity.HIGH -> Pair(GoldAccent, "HIGH")
        SubtaskSeverity.MEDIUM -> Pair(BlueAccent, "MEDIUM")
        SubtaskSeverity.LOW -> Pair(TextSecondary, "LOW")
    }

    Box(
        modifier = Modifier
            .background(color.copy(alpha = 0.12f), RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = label,
            color = color,
            style = MaterialTheme.typography.labelSmall,
            fontSize = 9.sp
        )
    }
}

@Composable
fun ProtectionBadge(status: ProtectionStatus) {
    val (color, label) = when (status) {
        ProtectionStatus.SECURED -> Pair(EmeraldSuccess, "SECURED")
        ProtectionStatus.ACKNOWLEDGED -> Pair(CyanAccent, "ACKNOWLEDGED")
        ProtectionStatus.UNDER_REVIEW -> Pair(GoldAccent, "UNDER REVIEW")
        ProtectionStatus.DISPUTE_FLAGGED -> Pair(RoseAlert, "DISPUTE FLAGGED")
    }

    Row(
        verticalAlignment = Alignment.CenterVertically,
        modifier = Modifier
            .background(color.copy(alpha = 0.15f), RoundedCornerShape(6.dp))
            .border(1.dp, color.copy(alpha = 0.35f), RoundedCornerShape(6.dp))
            .padding(horizontal = 7.dp, vertical = 3.dp)
    ) {
        Box(
            modifier = Modifier
                .size(6.dp)
                .background(color, CircleShape)
                .padding(end = 4.dp)
        )
        Text(
            text = "  $label",
            color = color,
            style = MaterialTheme.typography.labelSmall,
            fontSize = 10.sp
        )
    }
}

@Composable
fun HashBadge(hash: String, modifier: Modifier = Modifier) {
    val display = if (hash.length > 22) "${hash.take(12)}...${hash.takeLast(6)}" else hash
    Box(
        modifier = modifier
            .background(DarkNavy, RoundedCornerShape(4.dp))
            .border(1.dp, BorderSubtle, RoundedCornerShape(4.dp))
            .padding(horizontal = 6.dp, vertical = 2.dp)
    ) {
        Text(
            text = display,
            color = CyanAccent,
            style = MaterialTheme.typography.labelSmall,
            fontSize = 9.sp
        )
    }
}
