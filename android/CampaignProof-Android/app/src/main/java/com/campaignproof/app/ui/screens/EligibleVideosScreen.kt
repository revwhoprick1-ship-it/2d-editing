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
import com.campaignproof.app.data.local.EligibilityStatus
import com.campaignproof.app.data.local.ScannedVideoEntity
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.StatusAmber
import com.campaignproof.app.ui.theme.StatusGreen
import com.campaignproof.app.ui.theme.StatusRed
import com.campaignproof.app.ui.theme.SurfaceDark

@Composable
fun EligibleVideosScreen(
    videos: List<ScannedVideoEntity>,
    onStartRecordingQueue: (List<ScannedVideoEntity>) -> Unit,
    onTestRecording: () -> Unit = {}
) {
    var statusFilter by remember { mutableStateOf<EligibilityStatus?>(null) }
    var selectedIds by remember { mutableStateOf(setOf<String>()) }

    val filtered = videos.filter { statusFilter == null || it.eligibilityStatus == statusFilter }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Eligible Videos", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)

        Row(horizontalArrangement = Arrangement.spacedBy(6.dp), modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(onClick = { statusFilter = null }, modifier = Modifier.weight(1f)) { Text("All") }
            OutlinedButton(onClick = { statusFilter = EligibilityStatus.ELIGIBLE }, modifier = Modifier.weight(1f)) { Text("Green") }
            OutlinedButton(onClick = { statusFilter = EligibilityStatus.INSUFFICIENT_DATA }, modifier = Modifier.weight(1f)) { Text("Yellow") }
            OutlinedButton(onClick = { statusFilter = EligibilityStatus.NOT_ELIGIBLE }, modifier = Modifier.weight(1f)) { Text("Red") }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(
                onClick = {
                    selectedIds = videos.filter { it.eligibilityStatus == EligibilityStatus.ELIGIBLE }.map { it.id }.toSet()
                },
                modifier = Modifier.weight(1f)
            ) { Text("Select All Eligible") }
            Button(
                onClick = {
                    val queue = videos.filter { it.id in selectedIds }
                    if (queue.isNotEmpty()) onStartRecordingQueue(queue)
                },
                enabled = selectedIds.isNotEmpty(),
                modifier = Modifier.weight(1f)
            ) { Text("Record (${selectedIds.size})") }
        }

        OutlinedButton(onClick = onTestRecording, modifier = Modifier.fillMaxWidth()) {
            Text("TEST RECORDING (random video with audience data)")
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.weight(1f)) {
            items(filtered, key = { it.id }) { video ->
                val (label, color) = when (video.eligibilityStatus) {
                    EligibilityStatus.ELIGIBLE -> "Eligible" to StatusGreen
                    EligibilityStatus.INSUFFICIENT_DATA -> "Insufficient Data" to StatusAmber
                    EligibilityStatus.NOT_ELIGIBLE -> "Does Not Meet Requirements" to StatusRed
                }

                Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.small) {
                    Row(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.Top) {
                        Checkbox(
                            checked = video.id in selectedIds,
                            onCheckedChange = { checked ->
                                selectedIds = if (checked) selectedIds + video.id else selectedIds - video.id
                            }
                        )
                        Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            Text(video.title, fontWeight = FontWeight.SemiBold)
                            Text(
                                "${video.platform} · ${video.accountName} · Views: ${video.viewCount?.toString() ?: "Unavailable"}",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF94A3B8)
                            )
                            Text(
                                "${video.targetCountryCode}: ${video.targetCountryPercentage?.let { "${"%.1f".format(it)}%" } ?: "Unavailable"} · $label",
                                style = MaterialTheme.typography.bodySmall,
                                color = color,
                                fontWeight = FontWeight.Medium
                            )
                            Text(video.ruleSummary, style = MaterialTheme.typography.labelSmall, color = Color(0xFF64748B))
                        }
                    }
                }
            }
        }
    }
}
