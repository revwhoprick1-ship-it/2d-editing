package com.campaignproof.app.ui.screens

import android.content.Context
import android.content.Intent
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
import androidx.compose.material3.ButtonDefaults
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.campaignproof.app.automation.AccessibilityNavigationStatus
import com.campaignproof.app.automation.WorkflowSessionState
import com.campaignproof.app.data.local.RecordingEntity
import com.campaignproof.app.recording.RecorderState
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.StatusRed
import com.campaignproof.app.ui.theme.SurfaceDark
import java.io.File

@Composable
fun RecordingWorkflowScreen(
    session: WorkflowSessionState,
    recorderState: RecorderState,
    accessibilityStatus: AccessibilityNavigationStatus,
    onRequestMediaProjectionAndStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onStop: () -> Unit,
    onSkip: () -> Unit,
    onRetryNavigation: () -> Unit,
    onCancel: () -> Unit
) {
    var confirmedVisible by remember(session.currentIndex) { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Text("Recording Workflow", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        Text(session.progressLabel, color = Color(0xFF93C5FD), fontWeight = FontWeight.Medium)

        val current = session.currentVideo
        if (current == null) {
            Text(
                session.lastNavigationMessage.ifBlank { "Select eligible videos first to begin controlled evidence recording." },
                color = Color(0xFF94A3B8)
            )
            return
        }

        Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.medium) {
            Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Account: ${current.accountName} (${current.platform})", fontWeight = FontWeight.SemiBold)
                Text("Video: ${current.title}", color = Color(0xFFE2E8F0))
                Text("Navigation status: ${accessibilityStatus.detail}", style = MaterialTheme.typography.bodySmall, color = Color(0xFF94A3B8))
                if (session.lastNavigationMessage.isNotBlank()) {
                    Text(session.lastNavigationMessage, style = MaterialTheme.typography.bodySmall, color = Color(0xFF60A5FA))
                }
            }
        }

        // Mandatory safety confirmation gate: never silently record the wrong video
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = confirmedVisible, onCheckedChange = { confirmedVisible = it })
            Text(
                "I confirm the correct account, video title, and Audience Demographics are visible on screen.",
                style = MaterialTheme.typography.bodySmall
            )
        }

        when (recorderState) {
            RecorderState.IDLE -> {
                Button(
                    onClick = onRequestMediaProjectionAndStart,
                    enabled = confirmedVisible,
                    modifier = Modifier.fillMaxWidth()
                ) { Text("Start Recording (MediaProjection)") }
            }
            RecorderState.RECORDING -> {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedButton(onClick = onPause, modifier = Modifier.weight(1f)) { Text("Pause") }
                    Button(
                        onClick = onStop,
                        colors = ButtonDefaults.buttonColors(containerColor = StatusRed),
                        modifier = Modifier.weight(1f)
                    ) { Text("Stop & Save") }
                }
            }
            RecorderState.PAUSED -> {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                    Button(onClick = onResume, modifier = Modifier.weight(1f)) { Text("Resume") }
                    Button(
                        onClick = onStop,
                        colors = ButtonDefaults.buttonColors(containerColor = StatusRed),
                        modifier = Modifier.weight(1f)
                    ) { Text("Stop & Save") }
                }
            }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            OutlinedButton(onClick = onRetryNavigation, modifier = Modifier.weight(1f)) { Text("Retry Navigation") }
            OutlinedButton(onClick = onSkip, modifier = Modifier.weight(1f)) { Text("Skip Video") }
        }
        OutlinedButton(onClick = onCancel, modifier = Modifier.fillMaxWidth()) { Text("Cancel Session") }
    }
}

@Composable
fun RecordingsLibraryScreen(
    recordings: List<RecordingEntity>,
    onDeleteRecording: (RecordingEntity) -> Unit
) {
    val context = LocalContext.current

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Saved Recordings", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(
                "Stored locally for your review prior to Whop submission (CampaignProof/Platform/Account/Campaign/Video.mp4).",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF94A3B8)
            )
        }

        items(recordings, key = { it.id }) { rec ->
            Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.small) {
                Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(rec.videoTitle, fontWeight = FontWeight.SemiBold)
                    Text("${rec.platform} · ${rec.accountName} · ${rec.campaignName}", style = MaterialTheme.typography.bodySmall, color = Color(0xFF94A3B8))
                    Text(rec.relativePath, style = MaterialTheme.typography.labelSmall, color = Color(0xFF60A5FA))
                    Text(
                        "Views at scan: ${rec.viewCountAtScan?.toString() ?: "N/A"} · ${rec.targetCountryCode}: ${rec.targetCountryPercentage?.let { "${"%.1f".format(it)}%" } ?: "N/A"} · ${rec.durationSeconds}s",
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFFCBD5E1)
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedButton(onClick = { openVideoFile(context, rec.absoluteFilePath, Intent.ACTION_VIEW) }) { Text("Play") }
                        OutlinedButton(onClick = { openVideoFile(context, rec.absoluteFilePath, Intent.ACTION_SEND) }) { Text("Share") }
                        OutlinedButton(onClick = { onDeleteRecording(rec) }) { Text("Delete") }
                    }
                }
            }
        }
    }
}

private fun openVideoFile(context: Context, path: String, action: String) {
    val file = File(path)
    if (!file.exists()) return
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(action).apply {
        if (action == Intent.ACTION_VIEW) {
            setDataAndType(uri, "video/mp4")
        } else {
            type = "video/mp4"
            putExtra(Intent.EXTRA_STREAM, uri)
        }
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "CampaignProof Recording"))
}
