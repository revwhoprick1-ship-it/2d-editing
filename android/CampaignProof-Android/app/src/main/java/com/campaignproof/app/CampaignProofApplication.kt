package com.campaignproof.app

import android.app.Application
import com.campaignproof.app.automation.RecordingWorkflowController
import com.campaignproof.app.data.local.AppSettings
import com.campaignproof.app.data.local.CampaignProofDatabase
import com.campaignproof.app.data.local.SecureTokenStore
import com.campaignproof.app.data.remote.WhopApiClient
import com.campaignproof.app.data.remote.YouTubeAuthManager
import com.campaignproof.app.domain.VideoScannerRepository
import com.campaignproof.app.recording.RecordingStorageManager

class CampaignProofApplication : Application() {
    lateinit var database: CampaignProofDatabase
    lateinit var tokenStore: SecureTokenStore
    lateinit var settings: AppSettings
    lateinit var whopApi: WhopApiClient
    lateinit var youtubeAuthManager: YouTubeAuthManager
    lateinit var scannerRepository: VideoScannerRepository
    lateinit var workflowController: RecordingWorkflowController

    val crashFile get() = java.io.File(filesDir, "last_crash.txt")

    override fun onCreate() {
        super.onCreate()
        // Save any crash so the Setup tab can show it on next launch.
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, err ->
            runCatching {
                crashFile.writeText(
                    "${java.util.Date()}  thread=${thread.name}\n" + android.util.Log.getStackTraceString(err)
                )
            }
            previous?.uncaughtException(thread, err)
        }
        database = CampaignProofDatabase.getInstance(this)
        tokenStore = SecureTokenStore(this)
        settings = AppSettings(this)
        whopApi = WhopApiClient { settings.whopApiKey }
        youtubeAuthManager = YouTubeAuthManager(this) { settings.googleClientId }
        scannerRepository = VideoScannerRepository(database, tokenStore, youtubeAuthManager)
        workflowController = RecordingWorkflowController(this, RecordingStorageManager(this))
    }
}
