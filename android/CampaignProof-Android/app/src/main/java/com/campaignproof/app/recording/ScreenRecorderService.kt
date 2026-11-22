package com.campaignproof.app.recording

import android.app.Activity
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.MediaRecorder
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.io.File

enum class RecorderState { IDLE, RECORDING, PAUSED }

/**
 * Android Foreground Service (mediaProjection type) managing official MediaProjection
 * + VirtualDisplay + H.264 MediaRecorder with Pause, Resume, Stop, and clean teardown.
 */
class ScreenRecorderService : Service() {

    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var mediaRecorder: MediaRecorder? = null
    private var currentOutputPath: String? = null
    private var startedAtMs: Long = 0L

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START -> {
                val resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, Activity.RESULT_CANCELED)
                val resultData: Intent? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra(EXTRA_RESULT_DATA)
                }
                val outputPath = intent.getStringExtra(EXTRA_OUTPUT_PATH)
                val label = intent.getStringExtra(EXTRA_LABEL) ?: "Recording evidence"

                if (resultCode == Activity.RESULT_OK && resultData != null && !outputPath.isNullOrBlank()) {
                    startForegroundRecording(resultCode, resultData, outputPath, label)
                }
            }
            ACTION_PAUSE -> pauseRecording()
            ACTION_RESUME -> resumeRecording()
            ACTION_STOP -> stopRecordingAndRelease(cancelled = false)
            ACTION_CANCEL -> stopRecordingAndRelease(cancelled = true)
        }
        return START_NOT_STICKY
    }

    private fun startForegroundRecording(
        resultCode: Int,
        resultData: Intent,
        outputPath: String,
        label: String
    ) {
        ensureNotificationChannel()
        val notification = buildNotification(label)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        val metrics = resources.displayMetrics
        val width = (metrics.widthPixels / 2) * 2
        val height = (metrics.heightPixels / 2) * 2
        val densityDpi = metrics.densityDpi

        val projectionManager =
            getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val projection = projectionManager.getMediaProjection(resultCode, resultData)
            ?: run {
                stopSelf()
                return
            }

        projection.registerCallback(object : MediaProjection.Callback() {
            override fun onStop() {
                stopRecordingAndRelease(cancelled = false)
            }
        }, null)

        val recorder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(this)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }

        try {
            recorder.apply {
                setVideoSource(MediaRecorder.VideoSource.SURFACE)
                setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
                setVideoEncoder(MediaRecorder.VideoEncoder.H264)
                setVideoSize(width, height)
                setVideoFrameRate(30)
                setVideoEncodingBitRate(5_000_000)
                setOutputFile(outputPath)
                prepare()
            }

            virtualDisplay = projection.createVirtualDisplay(
                "CampaignProofCapture",
                width,
                height,
                densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                recorder.surface,
                null,
                null
            )

            recorder.start()
            mediaProjection = projection
            mediaRecorder = recorder
            currentOutputPath = outputPath
            startedAtMs = System.currentTimeMillis()
            _recorderState.value = RecorderState.RECORDING
        } catch (e: Exception) {
            _lastError.value = "MediaProjection start failed: ${e.message}"
            stopRecordingAndRelease(cancelled = true)
        }
    }

    private fun pauseRecording() {
        if (_recorderState.value != RecorderState.RECORDING) return
        runCatching {
            mediaRecorder?.pause()
            _recorderState.value = RecorderState.PAUSED
        }
    }

    private fun resumeRecording() {
        if (_recorderState.value != RecorderState.PAUSED) return
        runCatching {
            mediaRecorder?.resume()
            _recorderState.value = RecorderState.RECORDING
        }
    }

    private fun stopRecordingAndRelease(cancelled: Boolean) {
        val outputPath = currentOutputPath
        val durationSec = if (startedAtMs > 0L) {
            ((System.currentTimeMillis() - startedAtMs) / 1000L).toInt().coerceAtLeast(1)
        } else 0

        runCatching { mediaRecorder?.stop() }
        runCatching { mediaRecorder?.reset() }
        runCatching { mediaRecorder?.release() }
        runCatching { virtualDisplay?.release() }
        runCatching { mediaProjection?.stop() }

        mediaRecorder = null
        virtualDisplay = null
        mediaProjection = null
        currentOutputPath = null
        startedAtMs = 0L
        _recorderState.value = RecorderState.IDLE

        if (cancelled && outputPath != null) {
            runCatching { File(outputPath).delete() }
        } else if (!cancelled && outputPath != null) {
            _lastCompletedRecording.value = CompletedCapture(outputPath, durationSec)
        }

        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    private fun ensureNotificationChannel() {
        val mgr = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            CHANNEL_ID,
            "CampaignProof Screen Recording",
            NotificationManager.IMPORTANCE_LOW
        )
        mgr.createNotificationChannel(channel)
    }

    private fun buildNotification(label: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("CampaignProof Evidence Recording")
            .setContentText(label)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setOngoing(true)
            .build()
    }

    data class CompletedCapture(val outputPath: String, val durationSeconds: Int)

    companion object {
        private const val CHANNEL_ID = "campaignproof_recorder"
        private const val NOTIFICATION_ID = 4201

        const val ACTION_START = "com.campaignproof.action.START"
        const val ACTION_PAUSE = "com.campaignproof.action.PAUSE"
        const val ACTION_RESUME = "com.campaignproof.action.RESUME"
        const val ACTION_STOP = "com.campaignproof.action.STOP"
        const val ACTION_CANCEL = "com.campaignproof.action.CANCEL"

        const val EXTRA_RESULT_CODE = "result_code"
        const val EXTRA_RESULT_DATA = "result_data"
        const val EXTRA_OUTPUT_PATH = "output_path"
        const val EXTRA_LABEL = "label"

        private val _recorderState = MutableStateFlow(RecorderState.IDLE)
        val recorderState: StateFlow<RecorderState> = _recorderState.asStateFlow()

        private val _lastCompletedRecording = MutableStateFlow<CompletedCapture?>(null)
        val lastCompletedRecording: StateFlow<CompletedCapture?> = _lastCompletedRecording.asStateFlow()

        private val _lastError = MutableStateFlow<String?>(null)
        val lastError: StateFlow<String?> = _lastError.asStateFlow()

        fun clearCompletedEvent() {
            _lastCompletedRecording.value = null
        }
    }
}
