package com.campaignproof.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.campaignproof.app.data.local.AccountEntity
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.EligibilityStatus
import com.campaignproof.app.data.local.RecordingEntity
import com.campaignproof.app.data.local.ScannedVideoEntity
import com.campaignproof.app.ui.theme.AccentCobalt
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.StatusGreen
import com.campaignproof.app.ui.theme.SurfaceDark

@Composable
fun DashboardScreen(
    accounts: List<AccountEntity>,
    activeCampaign: CampaignEntity?,
    videos: List<ScannedVideoEntity>,
    recordings: List<RecordingEntity>,
    isScanning: Boolean,
    onScanAccounts: () -> Unit,
    onStartRecording: () -> Unit,
    onNavigateToAccounts: () -> Unit,
    onTestRecording: () -> Unit = {}
) {
    val eligibleCount = videos.count { it.eligibilityStatus == EligibilityStatus.ELIGIBLE }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Text(
                text = "CampaignProof",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = onScanAccounts,
                    enabled = !isScanning,
                    colors = ButtonDefaults.buttonColors(containerColor = AccentCobalt),
                    modifier = Modifier.weight(1f)
                ) {
                    Text(if (isScanning) "Scanning..." else "SCAN ACCOUNTS")
                }
                OutlinedButton(
                    onClick = onStartRecording,
                    enabled = eligibleCount > 0,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("START RECORDING")
                }
            }
            OutlinedButton(onClick = onTestRecording, modifier = Modifier.fillMaxWidth().padding(top = 8.dp)) {
                Text("TEST RECORDING (random video)")
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                MetricTile("Eligible Videos", eligibleCount.toString(), StatusGreen, Modifier.weight(1f))
                MetricTile("Completed Recordings", recordings.size.toString(), Color(0xFFF1F5F9), Modifier.weight(1f))
            }
        }

        item {
            Surface(
                color = SurfaceDark,
                border = BorderStroke(1.dp, BorderHairline),
                shape = MaterialTheme.shapes.medium,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("Active Campaign Requirements", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    if (activeCampaign != null) {
                        Text(activeCampaign.name, color = Color(0xFFCBD5E1))
                        Text(
                            "Platform: ${activeCampaign.platform} · Min Views: ${activeCampaign.minViews}" +
                                if (activeCampaign.minCountryPercentage > 0) " · ${activeCampaign.targetCountryName} >= ${activeCampaign.minCountryPercentage}%" else "",
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF94A3B8)
                        )
                        activeCampaign.whopRulesText?.let { rules ->
                            Text("Whop rules:", style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Medium)
                            Text(rules.take(400) + if (rules.length > 400) "…" else "", style = MaterialTheme.typography.bodySmall, color = Color(0xFFCBD5E1))
                        }
                    } else {
                        Text("No active campaign configured.", color = Color(0xFF94A3B8))
                    }
                }
            }
        }

        item {
            Surface(
                color = SurfaceDark,
                border = BorderStroke(1.dp, BorderHairline),
                shape = MaterialTheme.shapes.medium,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Connected Accounts (${accounts.size})", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        OutlinedButton(onClick = onNavigateToAccounts) { Text("Manage") }
                    }
                    if (accounts.isEmpty()) {
                        Text("No accounts connected yet. Connect YouTube (OAuth 2.0) or Instagram.", color = Color(0xFF94A3B8))
                    } else {
                        accounts.forEach { acc ->
                            Text("${acc.platform.name} · ${acc.name} (${acc.tokenStatus.name})", color = Color(0xFFE2E8F0))
                        }
                    }
                }
            }
        }

        item {
            Text("Recording History", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
        }

        if (recordings.isEmpty()) {
            item {
                Text("No recordings saved yet. Scan accounts and start a guided recording session.", color = Color(0xFF94A3B8))
            }
        } else {
            items(recordings.take(8)) { rec ->
                Surface(
                    color = SurfaceDark,
                    border = BorderStroke(1.dp, BorderHairline),
                    shape = MaterialTheme.shapes.small,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(rec.videoTitle, fontWeight = FontWeight.Medium)
                        Text("${rec.platform} · ${rec.accountName} · ${rec.relativePath}", style = MaterialTheme.typography.bodySmall, color = Color(0xFF94A3B8))
                    }
                }
            }
        }
    }
}

@Composable
private fun MetricTile(label: String, value: String, valueColor: Color, modifier: Modifier) {
    Surface(
        color = SurfaceDark,
        border = BorderStroke(1.dp, BorderHairline),
        shape = MaterialTheme.shapes.medium,
        modifier = modifier
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(label, style = MaterialTheme.typography.bodySmall, color = Color(0xFF94A3B8))
            Spacer(modifier = Modifier.height(4.dp))
            Text(value, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = valueColor)
        }
    }
}
