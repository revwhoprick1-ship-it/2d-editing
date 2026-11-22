package com.campaignproof.app.ui.viewmodel

import android.app.Application
import android.content.Intent
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.campaignproof.app.CampaignProofApplication
import com.campaignproof.app.data.local.AccountEntity
import com.campaignproof.app.data.local.AppSettingsState
import com.campaignproof.app.data.local.AuthMode
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.CampaignPlatform
import com.campaignproof.app.data.local.Platform
import com.campaignproof.app.data.local.RecordingEntity
import com.campaignproof.app.data.local.ScannedVideoEntity
import com.campaignproof.app.data.local.TokenStatus
import com.campaignproof.app.data.remote.ApiClientFactory
import com.campaignproof.app.data.remote.WhopCampaignInfo
import com.campaignproof.app.domain.ParsedWhopRules
import com.campaignproof.app.domain.WhopRuleParser
import com.campaignproof.app.recording.ScreenRecorderService
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.io.File
import java.util.UUID

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val app = application as CampaignProofApplication
    private val db = app.database

    val accounts = db.accountDao().observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val campaigns = db.campaignDao().observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val videos = db.scannedVideoDao().observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val recordings = db.recordingDao().observeAll()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val workflowSession = app.workflowController.session
    val recorderState = ScreenRecorderService.recorderState

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()

    val settings: StateFlow<AppSettingsState> = app.settings.state

    private val _whopImport = MutableStateFlow<WhopImportState>(WhopImportState.Idle)
    val whopImport: StateFlow<WhopImportState> = _whopImport.asStateFlow()

    private val _statusBanner = MutableStateFlow<String?>(null)
    val statusBanner: StateFlow<String?> = _statusBanner.asStateFlow()

    init {
        viewModelScope.launch {
            if (db.campaignDao().getActive() == null) {
                db.campaignDao().upsert(
                    CampaignEntity(
                        id = "camp_default_us",
                        name = "Whop US Clipping — 10K / 50% US",
                        platform = CampaignPlatform.YOUTUBE,
                        minViews = 10_000L,
                        targetCountryCode = "US",
                        targetCountryName = "United States",
                        minCountryPercentage = 50.0,
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
            }
        }

        // Persist completed screen recordings to Room automatically
        viewModelScope.launch {
            ScreenRecorderService.lastCompletedRecording.collect { capture ->
                if (capture != null) {
                    val entity = app.workflowController.buildRecordingEntity(capture.durationSeconds)
                    if (entity != null) {
                        db.recordingDao().upsert(entity)
                        _statusBanner.value = "Saved recording: ${entity.relativePath}"
                        app.workflowController.advanceToNextVideo(wasRecorded = true)
                    }
                    ScreenRecorderService.clearCompletedEvent()
                }
            }
        }
    }

    fun handleGoogleOAuthIntentResult(intent: Intent) {
        viewModelScope.launch {
            runCatching {
                val bundle = app.youtubeAuthManager.handleAuthResult(intent)
                val channels = ApiClientFactory.youtubeDataApi
                    .getMyChannels("Bearer ${bundle.accessToken}").items
                if (channels.isEmpty()) {
                    _statusBanner.value = "No YouTube channels found on the selected Google account."
                    return@runCatching
                }
                for (ch in channels) {
                    val accId = "yt_${ch.id}"
                    app.tokenStore.saveTokens(accId, bundle)
                    db.accountDao().upsert(
                        AccountEntity(
                            id = accId,
                            platform = Platform.YOUTUBE,
                            externalId = ch.id,
                            name = ch.snippet?.title ?: "YouTube Channel",
                            handle = ch.snippet?.customUrl ?: ch.id,
                            avatarUrl = ch.snippet?.thumbnails?.medium?.url,
                            subscriberCount = ch.statistics?.subscriberCount?.toLongOrNull(),
                            uploadsPlaylistId = ch.contentDetails?.relatedPlaylists?.uploads,
                            authMode = AuthMode.GOOGLE_OAUTH,
                            tokenStatus = TokenStatus.ACTIVE,
                            selectedForScan = true,
                            connectedAtEpochMs = System.currentTimeMillis()
                        )
                    )
                }
                _statusBanner.value = "Connected ${channels.size} YouTube channel(s)."
            }.onFailure { err ->
                _statusBanner.value = err.message ?: "Google OAuth failed"
            }
        }
    }

    fun addManualInstagramAccount(handle: String, displayName: String) {
        val clean = handle.trim().removePrefix("@")
        if (clean.isEmpty()) return
        viewModelScope.launch {
            db.accountDao().upsert(
                AccountEntity(
                    id = "ig_man_${UUID.randomUUID().toString().take(8)}",
                    platform = Platform.INSTAGRAM,
                    externalId = "manual_$clean",
                    name = displayName.ifBlank { "@$clean" },
                    handle = "@$clean",
                    avatarUrl = null,
                    subscriberCount = null,
                    uploadsPlaylistId = null,
                    authMode = AuthMode.MANUAL_FALLBACK,
                    tokenStatus = TokenStatus.MANUAL_ONLY,
                    selectedForScan = true,
                    connectedAtEpochMs = System.currentTimeMillis()
                )
            )
            _statusBanner.value = "Added Instagram manual-fallback account @$clean"
        }
    }

    fun toggleAccountSelection(account: AccountEntity) {
        viewModelScope.launch {
            db.accountDao().setSelectedForScan(account.id, !account.selectedForScan)
        }
    }

    fun removeAccount(accountId: String) {
        viewModelScope.launch {
            app.tokenStore.deleteTokens(accountId)
            db.scannedVideoDao().deleteByAccount(accountId)
            db.accountDao().deleteById(accountId)
        }
    }

    fun saveCampaign(campaign: CampaignEntity) {
        viewModelScope.launch {
            db.campaignDao().upsert(campaign)
            if (campaign.isActive) {
                db.campaignDao().activateCampaign(campaign.id)
            }
            _statusBanner.value = "Saved campaign \"${campaign.name}\""
        }
    }

    fun activateCampaign(id: String) {
        viewModelScope.launch { db.campaignDao().activateCampaign(id) }
    }

    fun scanAccounts() {
        if (_isScanning.value) return
        viewModelScope.launch {
            _isScanning.value = true
            try {
                val active = db.campaignDao().getActive()
                if (active == null) {
                    _statusBanner.value = "Configure an active campaign first."
                    return@launch
                }
                val results = app.scannerRepository.scanAllSelectedAccounts(active)
                val total = results.sumOf { it.videosFound }
                _statusBanner.value = "Scan complete across ${results.size} account(s): $total videos evaluated."
            } finally {
                _isScanning.value = false
            }
        }
    }

    fun startRecordingSession(selectedVideos: List<ScannedVideoEntity>) {
        viewModelScope.launch {
            val active = db.campaignDao().getActive() ?: return@launch
            app.workflowController.startSession(selectedVideos, active)
        }
    }

    fun confirmEvidenceAndStartCapture(resultCode: Int, data: Intent) {
        app.workflowController.setUserConfirmedEvidence(true)
        app.workflowController.startRecording(resultCode, data)
    }

    fun pauseRecording() = app.workflowController.pauseRecording()
    fun resumeRecording() = app.workflowController.resumeRecording()
    fun stopRecording() = app.workflowController.stopRecording()
    fun cancelRecording() = app.workflowController.cancelRecording()
    fun skipVideo() = app.workflowController.advanceToNextVideo(wasRecorded = false)
    fun retryNavigation() = app.workflowController.launchNavigationForCurrent()

    fun deleteRecording(recording: RecordingEntity) {
        viewModelScope.launch {
            runCatching { File(recording.absoluteFilePath).delete() }
            db.recordingDao().deleteById(recording.id)
        }
    }

    fun saveSettings(newState: AppSettingsState) {
        app.settings.save(newState)
        _statusBanner.value = "Setup saved on this device."
    }

    fun showBanner(msg: String) {
        _statusBanner.value = msg
    }

    fun lookupWhop(input: String) {
        if (_whopImport.value is WhopImportState.Loading) return
        viewModelScope.launch {
            _whopImport.value = WhopImportState.Loading
            _whopImport.value = runCatching {
                val info = app.whopApi.lookup(input)
                val parsed = WhopRuleParser.parse(info.title + "\n" + info.description, info.extraFields)
                WhopImportState.Found(info, parsed)
            }.getOrElse { WhopImportState.Error(it.message ?: "Whop lookup failed") }
        }
    }

    fun clearWhopImport() {
        _whopImport.value = WhopImportState.Idle
    }

    fun clearBanner() {
        _statusBanner.value = null
    }
}

sealed interface WhopImportState {
    data object Idle : WhopImportState
    data object Loading : WhopImportState
    data class Found(val info: WhopCampaignInfo, val parsed: ParsedWhopRules) : WhopImportState
    data class Error(val message: String) : WhopImportState
}
