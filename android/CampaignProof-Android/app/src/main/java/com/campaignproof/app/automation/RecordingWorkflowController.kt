package com.campaignproof.app.automation

import android.content.Context
import android.content.Intent
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.RecordingEntity
import com.campaignproof.app.data.local.RecordingStatus
import com.campaignproof.app.data.local.ScannedVideoEntity
import com.campaignproof.app.recording.RecordingFileLocation
import com.campaignproof.app.recording.RecordingStorageManager
import com.campaignproof.app.recording.ScreenRecorderService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File
import java.util.UUID

data class WorkflowSessionState(
    val active: Boolean = false,
    val queue: List<ScannedVideoEntity> = emptyList(),
    val currentIndex: Int = 0,
    val userConfirmedEvidenceVisible: Boolean = false,
    val lastNavigationMessage: String = "",
    val completedCount: Int = 0
) {
    val currentVideo: ScannedVideoEntity? get() = queue.getOrNull(currentIndex)
    val progressLabel: String
        get() = if (queue.isEmpty()) "No videos queued"
        else "Recording ${currentIndex + 1} of ${queue.size} eligible videos"
}

class RecordingWorkflowController(
    private val context: Context,
    private val storageManager: RecordingStorageManager
) {
    private val _session = MutableStateFlow(WorkflowSessionState())
    val session: StateFlow<WorkflowSessionState> = _session.asStateFlow()

    private var pendingLocation: RecordingFileLocation? = null
    private var activeCampaign: CampaignEntity? = null

    fun startSession(videos: List<ScannedVideoEntity>, campaign: CampaignEntity) {
        if (videos.isEmpty()) return
        activeCampaign = campaign
        _session.value = WorkflowSessionState(
            active = true,
            queue = videos,
            currentIndex = 0,
            userConfirmedEvidenceVisible = false,
            lastNavigationMessage = "Ready to open analytics for video 1 of ${videos.size}"
        )
        launchNavigationForCurrent()
    }

    fun launchNavigationForCurrent() {
        val current = _session.value.currentVideo ?: return
        CampaignProofAccessibilityService.setNavigationTarget(
            NavigationTarget(
                platform = current.platform.name,
                expectedAccountName = current.accountName,
                expectedVideoTitle = current.title
            )
        )
        val result = StudioNavigationLauncher.openVideoAnalytics(context, current)
        _session.value = _session.value.copy(
            userConfirmedEvidenceVisible = false,
            lastNavigationMessage = result.getOrElse { "Intent failed: ${it.message}. Complete step manually." }
        )
    }

    fun setUserConfirmedEvidence(confirmed: Boolean) {
        _session.value = _session.value.copy(userConfirmedEvidenceVisible = confirmed)
    }

    fun startRecording(mediaProjectionResultCode: Int, mediaProjectionData: Intent) {
        val state = _session.value
        val video = state.currentVideo ?: return
        val campaign = activeCampaign ?: return
        require(state.userConfirmedEvidenceVisible) {
            "User must confirm the correct video and Audience Demographics are visible before recording."
        }

        val loc = storageManager.createTargetRecordingFile(
            platform = video.platform,
            accountName = video.accountName,
            campaignName = campaign.name,
            videoTitle = video.title,
            externalVideoId = video.externalVideoId
        )
        pendingLocation = loc

        val intent = Intent(context, ScreenRecorderService::class.java).apply {
            action = ScreenRecorderService.ACTION_START
            putExtra(ScreenRecorderService.EXTRA_RESULT_CODE, mediaProjectionResultCode)
            putExtra(ScreenRecorderService.EXTRA_RESULT_DATA, mediaProjectionData)
            putExtra(ScreenRecorderService.EXTRA_OUTPUT_PATH, loc.file.absolutePath)
            putExtra(ScreenRecorderService.EXTRA_LABEL, "${state.progressLabel}: ${video.title}")
        }
        context.startForegroundService(intent)
    }

    fun pauseRecording() {
        context.startService(
            Intent(context, ScreenRecorderService::class.java).setAction(ScreenRecorderService.ACTION_PAUSE)
        )
    }

    fun resumeRecording() {
        context.startService(
            Intent(context, ScreenRecorderService::class.java).setAction(ScreenRecorderService.ACTION_RESUME)
        )
    }

    fun stopRecording() {
        context.startService(
            Intent(context, ScreenRecorderService::class.java).setAction(ScreenRecorderService.ACTION_STOP)
        )
    }

    fun cancelRecording() {
        context.startService(
            Intent(context, ScreenRecorderService::class.java).setAction(ScreenRecorderService.ACTION_CANCEL)
        )
        CampaignProofAccessibilityService.setNavigationTarget(null)
        _session.value = WorkflowSessionState()
    }

    fun buildRecordingEntity(durationSeconds: Int): RecordingEntity? {
        val video = _session.value.currentVideo ?: return null
        val campaign = activeCampaign ?: return null
        val loc = pendingLocation ?: return null
        val fileSize = File(loc.file.absolutePath).takeIf { it.exists() }?.length() ?: 0L
        return RecordingEntity(
            id = "rec_${UUID.randomUUID().toString().take(8)}",
            videoId = video.id,
            externalVideoId = video.externalVideoId,
            videoTitle = video.title,
            videoUrl = video.videoUrl,
            platform = video.platform,
            accountId = video.accountId,
            accountName = video.accountName,
            campaignId = campaign.id,
            campaignName = campaign.name,
            relativePath = loc.relativePath,
            absoluteFilePath = loc.file.absolutePath,
            fileSizeBytes = fileSize,
            durationSeconds = durationSeconds,
            viewCountAtScan = video.viewCount,
            targetCountryCode = video.targetCountryCode,
            targetCountryPercentage = video.targetCountryPercentage,
            demographicsSummary = video.demographicsJson.ifBlank { "Demographics unavailable from API" },
            campaignRequirementsSnapshotJson = "Platform=${campaign.platform};MinViews=${campaign.minViews};${campaign.targetCountryCode}>=${campaign.minCountryPercentage}%",
            recordedAtEpochMs = System.currentTimeMillis(),
            status = RecordingStatus.COMPLETED
        )
    }

    fun advanceToNextVideo(wasRecorded: Boolean) {
        val state = _session.value
        val nextIndex = state.currentIndex + 1
        val completed = state.completedCount + if (wasRecorded) 1 else 0
        if (nextIndex >= state.queue.size) {
            CampaignProofAccessibilityService.setNavigationTarget(null)
            _session.value = state.copy(
                active = false,
                completedCount = completed,
                lastNavigationMessage = "Session complete: $completed recording(s) saved locally for review."
            )
        } else {
            _session.value = state.copy(
                currentIndex = nextIndex,
                completedCount = completed,
                userConfirmedEvidenceVisible = false
            )
            launchNavigationForCurrent()
        }
    }
}
