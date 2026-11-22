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
    val completedCount: Int = 0,
    /** True = UI should immediately ask Android for screen-record permission and start. */
    val pendingAutoStart: Boolean = false
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
            lastNavigationMessage = "Starting screen recording…",
            pendingAutoStart = true
        )
    }

    fun consumeAutoStart() {
        _session.value = _session.value.copy(pendingAutoStart = false)
    }

    /** Called once recording has started: phone is driven Home -> Play Store -> app -> video -> Audience. */
    private fun runAutomationForCurrent() {
        val current = _session.value.currentVideo ?: return
        val target = NavigationTarget(
            platform = current.platform.name,
            expectedAccountName = current.accountName,
            expectedVideoTitle = current.title,
            deepLinkUrl = if (current.platform.name == "YOUTUBE") current.studioAnalyticsUrl else current.videoUrl
        )
        val started = CampaignProofAccessibilityService.runAutomation(target) { ok, msg ->
            _session.value = _session.value.copy(lastNavigationMessage = msg)
            // Stop + save the recording, then come back to the app
            stopRecording()
            CampaignProofAccessibilityService.bringAppToFront()
        }
        _session.value = _session.value.copy(
            lastNavigationMessage = if (started) "Recording… automation running"
            else "Automation is OFF: enable CampaignProof in Settings > Accessibility. Recording continues — navigate manually, then Stop & Save."
        )
    }

    fun launchNavigationForCurrent() {
        if (ScreenRecorderService.recorderState.value != com.campaignproof.app.recording.RecorderState.IDLE) {
            runAutomationForCurrent()
            return
        }
        _session.value = _session.value.copy(pendingAutoStart = true)
    }

    @Suppress("unused")
    private fun legacyOpenDirect() {
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
        // Give the recorder a moment to start, then drive the phone
        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({ runAutomationForCurrent() }, 1500)
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
                userConfirmedEvidenceVisible = false,
                lastNavigationMessage = "Next video: asking to record…",
                pendingAutoStart = true
            )
        }
    }
}
