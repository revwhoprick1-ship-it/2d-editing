package com.campaignproof.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.campaignproof.app.data.local.AccountEntity
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.CampaignPlatform
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.SurfaceDark
import java.util.UUID

@Composable
fun AccountsScreen(
    accounts: List<AccountEntity>,
    onConnectYouTube: () -> Unit,
    onAddManualInstagram: (handle: String, displayName: String) -> Unit,
    onToggleAccount: (AccountEntity) -> Unit,
    onRemoveAccount: (String) -> Unit
) {
    var igHandle by remember { mutableStateOf("") }
    var igName by remember { mutableStateOf("") }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Connected Accounts", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(
                "Connect multiple YouTube channels via official Google OAuth 2.0 (passwords are never collected).",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF94A3B8)
            )
            Button(onClick = onConnectYouTube, modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) {
                Text("Connect YouTube Channel (Google OAuth 2.0)")
            }
        }

        item {
            Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.medium) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Instagram Manual Navigation Fallback", fontWeight = FontWeight.SemiBold)
                    OutlinedTextField(
                        value = igHandle,
                        onValueChange = { igHandle = it },
                        label = { Text("Instagram @handle") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = igName,
                        onValueChange = { igName = it },
                        label = { Text("Display Name (optional)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedButton(
                        onClick = {
                            if (igHandle.isNotBlank()) {
                                onAddManualInstagram(igHandle, igName)
                                igHandle = ""
                                igName = ""
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Add Instagram Fallback Account")
                    }
                }
            }
        }

        items(accounts, key = { it.id }) { acc ->
            Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.small) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.weight(1f)) {
                        Checkbox(checked = acc.selectedForScan, onCheckedChange = { onToggleAccount(acc) })
                        Column {
                            Text(acc.name, fontWeight = FontWeight.SemiBold)
                            Text("${acc.platform} · ${acc.handle} · ${acc.tokenStatus}", style = MaterialTheme.typography.bodySmall, color = Color(0xFF94A3B8))
                        }
                    }
                    OutlinedButton(onClick = { onRemoveAccount(acc.id) }) { Text("Remove") }
                }
            }
        }
    }
}

@Composable
fun CampaignsScreen(
    campaigns: List<CampaignEntity>,
    onSaveCampaign: (CampaignEntity) -> Unit,
    onActivateCampaign: (String) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var minViews by remember { mutableStateOf("10000") }
    var countryCode by remember { mutableStateOf("US") }
    var minCountryPct by remember { mutableStateOf("50") }
    var platform by remember { mutableStateOf(CampaignPlatform.YOUTUBE) }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Campaign Requirements", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        }

        item {
            Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.medium) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Create New Whop Campaign Rule", fontWeight = FontWeight.SemiBold)
                    OutlinedTextField(value = name, onValueChange = { name = it }, label = { Text("Campaign Name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        CampaignPlatform.entries.forEach { p ->
                            OutlinedButton(onClick = { platform = p }, modifier = Modifier.weight(1f)) {
                                Text(if (platform == p) "* ${p.name}" else p.name)
                            }
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(value = minViews, onValueChange = { minViews = it }, label = { Text("Min Views") }, singleLine = true, modifier = Modifier.weight(1f))
                        OutlinedTextField(value = countryCode, onValueChange = { countryCode = it.uppercase().take(2) }, label = { Text("Country ISO") }, singleLine = true, modifier = Modifier.weight(0.7f))
                        OutlinedTextField(value = minCountryPct, onValueChange = { minCountryPct = it }, label = { Text("Min %") }, singleLine = true, modifier = Modifier.weight(0.8f))
                    }
                    Button(
                        onClick = {
                            if (name.isNotBlank()) {
                                onSaveCampaign(
                                    CampaignEntity(
                                        id = "camp_${UUID.randomUUID().toString().take(8)}",
                                        name = name.trim(),
                                        platform = platform,
                                        minViews = minViews.toLongOrNull() ?: 10_000L,
                                        targetCountryCode = countryCode.ifBlank { "US" },
                                        targetCountryName = countryCode.ifBlank { "US" },
                                        minCountryPercentage = minCountryPct.toDoubleOrNull() ?: 50.0,
                                        requiredAgeGroupsCsv = "",
                                        minAgeGroupPercentage = null,
                                        requiredGender = "ANY",
                                        minGenderPercentage = null,
                                        shortsOrReelsOnly = true,
                                        publishedAfterIso = null,
                                        requiredKeyword = null,
                                        isActive = true,
                                        updatedAtEpochMs = System.currentTimeMillis()
                                    )
                                )
                                name = ""
                            }
                        },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Save & Activate Campaign")
                    }
                }
            }
        }

        items(campaigns, key = { it.id }) { camp ->
            Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.small) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(camp.name, fontWeight = FontWeight.SemiBold)
                        Text(
                            "${camp.platform} · >= ${camp.minViews} views · ${camp.targetCountryCode} >= ${camp.minCountryPercentage}%",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF94A3B8)
                        )
                    }
                    if (!camp.isActive) {
                        OutlinedButton(onClick = { onActivateCampaign(camp.id) }) { Text("Activate") }
                    } else {
                        Text("Active", color = Color(0xFF4ADE80), fontWeight = FontWeight.Medium)
                    }
                }
            }
        }
    }
}
