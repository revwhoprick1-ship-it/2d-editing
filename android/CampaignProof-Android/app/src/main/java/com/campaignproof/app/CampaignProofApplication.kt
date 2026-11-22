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

    override fun onCreate() {
        super.onCreate()
        database = CampaignProofDatabase.getInstance(this)
        tokenStore = SecureTokenStore(this)
        settings = AppSettings(this)
        whopApi = WhopApiClient { settings.whopApiKey }
        youtubeAuthManager = YouTubeAuthManager(this) { settings.googleClientId }
        scannerRepository = VideoScannerRepository(database, tokenStore, youtubeAuthManager)
        workflowController = RecordingWorkflowController(this, RecordingStorageManager(this))
    }
}
