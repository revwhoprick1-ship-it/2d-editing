package com.campaignproof.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.CampaignPlatform
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.StatusAmber
import com.campaignproof.app.ui.theme.StatusRed
import com.campaignproof.app.ui.theme.SurfaceDark
import com.campaignproof.app.ui.viewmodel.WhopImportState

@Composable
fun WhopImportCard(
    state: WhopImportState,
    onLookup: (String) -> Unit,
    onClear: () -> Unit,
    onSaveCampaign: (CampaignEntity) -> Unit
) {
    var input by remember { mutableStateOf("") }
    val clipboard = LocalClipboardManager.current

    Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.medium) {
        Column(modifier = Modifier.padding(14.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("Import from Whop Content Rewards", fontWeight = FontWeight.SemiBold)
            Text(
                "Paste a submission ID (btys_…), a campaign ID, or a whop.com link.",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF94A3B8)
            )
            OutlinedTextField(
                value = input,
                onValueChange = { input = it },
                label = { Text("Submission / campaign ID") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth()
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = {
                    clipboard.getText()?.text?.let { input = it.trim() }
                }) { Text("Paste") }
                Button(
                    onClick = { onLookup(input) },
                    enabled = input.isNotBlank() && state !is WhopImportState.Loading,
                    modifier = Modifier.weight(1f)
                ) { Text("Get campaign rules") }
            }

            when (state) {
                WhopImportState.Idle -> Unit
                WhopImportState.Loading -> Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(modifier = Modifier.padding(end = 8.dp))
                    Text("Asking Whop…")
                }
                is WhopImportState.Error -> Text(state.message, color = StatusRed)
                is WhopImportState.Found -> FoundSection(state, onClear) {
                    onSaveCampaign(it)
                    onClear()
                    input = ""
                }
            }
        }
    }
}

@Composable
private fun FoundSection(
    state: WhopImportState.Found,
    onClear: () -> Unit,
    onSave: (CampaignEntity) -> Unit
) {
    val info = state.info
    val p = state.parsed
    var name by remember(info) { mutableStateOf(info.title) }
    var minViews by remember(info) { mutableStateOf(p.minViews?.toString().orEmpty()) }
    var country by remember(info) { mutableStateOf(p.countryCode.orEmpty()) }
    var pct by remember(info) { mutableStateOf(p.minCountryPercentage?.let { trimNum(it) }.orEmpty()) }
    var platform by remember(info) { mutableStateOf(p.platform ?: CampaignPlatform.BOTH) }
    var shortsOnly by remember(info) { mutableStateOf(p.shortsOnly ?: true) }
    var showAll by remember(info) { mutableStateOf(false) }

    Text(info.title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
    Text(
        listOfNotNull("Campaign ${info.bountyId}", info.status?.let { "status: $it" }, info.submissionId?.let { "from submission $it" })
            .joinToString(" · "),
        style = MaterialTheme.typography.bodySmall,
        color = Color(0xFF94A3B8)
    )

    if (info.description.isNotBlank()) {
        Text("Rules (from Whop):", fontWeight = FontWeight.Medium)
        SelectionContainer {
            Text(
                if (showAll || info.description.length <= 600) info.description else info.description.take(600) + "…",
                style = MaterialTheme.typography.bodySmall
            )
        }
    } else {
        Text("Whop returned no rules text for this campaign.", color = StatusAmber)
    }

    if (info.extraFields.isNotEmpty() || info.submissionLinks.isNotEmpty()) {
        TextButton(onClick = { showAll = !showAll }) { Text(if (showAll) "Hide details" else "Show all Whop fields") }
        if (showAll) {
            SelectionContainer {
                Text(
                    (info.extraFields.map { "${it.first}: ${it.second}" } +
                        info.submissionLinks.map { "submission link: $it" }).joinToString("\n"),
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFFCBD5E1)
                )
            }
        }
    }

    p.notes.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall, color = StatusAmber) }
    Text(
        "Check these values against the rules above. Empty = not found in Whop text, fill in yourself.",
        style = MaterialTheme.typography.bodySmall,
        color = Color(0xFF94A3B8)
    )

    OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Campaign name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        CampaignPlatform.entries.forEach { cp ->
            OutlinedButton(onClick = { platform = cp }, modifier = Modifier.weight(1f)) {
                Text(if (platform == cp) "* ${cp.name}" else cp.name)
            }
        }
    }
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(value = minViews, onValueChange = { minViews = it.filter(Char::isDigit) }, label = { Text("Min views") }, singleLine = true, modifier = Modifier.weight(1f))
        OutlinedTextField(value = country, onValueChange = { country = it.uppercase().take(2) }, label = { Text("Country") }, singleLine = true, modifier = Modifier.weight(0.7f))
        OutlinedTextField(value = pct, onValueChange = { pct = it }, label = { Text("Min %") }, singleLine = true, modifier = Modifier.weight(0.8f))
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        Switch(checked = shortsOnly, onCheckedChange = { shortsOnly = it })
        Text("  Shorts / Reels only")
    }

    val canSave = name.isNotBlank() && minViews.toLongOrNull() != null
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(onClick = onClear) { Text("Cancel") }
        Button(
            enabled = canSave,
            modifier = Modifier.weight(1f),
            onClick = {
                val countryCode = country.ifBlank { "US" }
                onSave(
                    CampaignEntity(
                        id = "whop_${info.bountyId}",
                        name = name.trim(),
                        platform = platform,
                        minViews = minViews.toLong(),
                        targetCountryCode = countryCode,
                        targetCountryName = countryCode,
                        // 0 = no country rule (evaluator skips it)
                        minCountryPercentage = if (country.isBlank()) 0.0 else pct.toDoubleOrNull() ?: 0.0,
                        requiredAgeGroupsCsv = "",
                        minAgeGroupPercentage = null,
                        requiredGender = "ANY",
                        minGenderPercentage = null,
                        shortsOrReelsOnly = shortsOnly,
                        publishedAfterIso = null,
                        requiredKeyword = null,
                        isActive = true,
                        updatedAtEpochMs = System.currentTimeMillis(),
                        whopBountyId = info.bountyId,
                        whopSubmissionId = info.submissionId,
                        whopRulesText = info.description.ifBlank { null }
                    )
                )
            }
        ) { Text("Save & Activate") }
    }
    if (!canSave) Text("Enter min views to save.", style = MaterialTheme.typography.bodySmall, color = StatusAmber)
}

private fun trimNum(d: Double): String = if (d % 1.0 == 0.0) d.toLong().toString() else d.toString()
