package com.campaignproof.app.recording

import android.content.Context
import android.os.Environment
import com.campaignproof.app.data.local.Platform
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class RecordingFileLocation(
    val file: File,
    val relativePath: String
)

/**
 * Organizes local MP4 evidence recordings strictly as:
 * CampaignProof/<Platform>/<Account>/<Campaign>/<Video>.mp4
 */
class RecordingStorageManager(private val context: Context) {

    fun createTargetRecordingFile(
        platform: Platform,
        accountName: String,
        campaignName: String,
        videoTitle: String,
        externalVideoId: String
    ): RecordingFileLocation {
        val platformDir = if (platform == Platform.YOUTUBE) "YouTube" else "Instagram"
        val safeAccount = sanitize(accountName, "Account")
        val safeCampaign = sanitize(campaignName, "Campaign")
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val safeVideo = "${sanitize(videoTitle, "Video")}_${sanitize(externalVideoId, "id")}_$stamp.mp4"

        val baseRoot = File(
            context.getExternalFilesDir(Environment.DIRECTORY_MOVIES) ?: context.filesDir,
            "CampaignProof"
        )
        val dir = File(File(File(baseRoot, platformDir), safeAccount), safeCampaign)
        if (!dir.exists()) {
            dir.mkdirs()
        }

        val targetFile = File(dir, safeVideo)
        val relative = "CampaignProof/$platformDir/$safeAccount/$safeCampaign/$safeVideo"
        return RecordingFileLocation(targetFile, relative)
    }

    private fun sanitize(raw: String, fallback: String): String {
        val cleaned = raw.replace(Regex("[^A-Za-z0-9_\\- ]"), "")
            .trim()
            .replace(Regex("\\s+"), "_")
            .take(56)
        return cleaned.ifEmpty { fallback }
    }
}
