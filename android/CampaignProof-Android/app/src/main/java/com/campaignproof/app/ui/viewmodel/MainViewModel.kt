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

    /** Test run: pick one random scanned video that has audience data and open the recording flow. */
    fun startTestRecording(): Boolean {
        val all = videos.value
        if (all.isEmpty()) {
            _statusBanner.value = "No videos yet. Connect an account and tap SCAN ACCOUNTS first."
            return false
        }
        val withData = all.filter {
            it.demographicsAvailable || it.targetCountryPercentage != null ||
                (it.countryBreakdownJson.isNotBlank() && it.countryBreakdownJson != "[]" && it.countryBreakdownJson != "{}")
        }
        val pick = (withData.ifEmpty { all }).random()
        _statusBanner.value = if (withData.isEmpty())
            "TEST: no video has audience data yet, using random video \"${pick.title}\""
        else
            "TEST recording: \"${pick.title}\""
        viewModelScope.launch {
            val campaign = db.campaignDao().getActive() ?: return@launch
            app.workflowController.startSession(listOf(pick), campaign)
        }
        return true
    }

    fun confirmEvidenceAndStartCapture(resultCode: Int, data: Intent) {
        app.workflowController.setUserConfirmedEvidence(true)
        app.workflowController.startRecording(resultCode, data)
    }

    fun consumeAutoStart() = app.workflowController.consumeAutoStart()

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

    private val _testLog = MutableStateFlow(readCrash())
    val testLog: StateFlow<String> = _testLog.asStateFlow()
    private val _isTesting = MutableStateFlow(false)
    val isTesting: StateFlow<Boolean> = _isTesting.asStateFlow()

    private fun readCrash(): String = runCatching {
        val f = app.crashFile
        if (f.exists()) "LAST CRASH (send this to support):\n" + f.readText().take(4000) else ""
    }.getOrDefault("")

    private fun log(line: String) {
        _testLog.value = (_testLog.value + "\n" + line).trim()
    }

    fun clearTestLog() {
        runCatching { app.crashFile.delete() }
        _testLog.value = ""
    }

    fun reportError(where: String, t: Throwable) {
        log("ERROR in $where: ${t.javaClass.simpleName}: ${t.message}\n" + android.util.Log.getStackTraceString(t).take(1500))
        _statusBanner.value = "$where failed: ${t.message ?: t.javaClass.simpleName} (details in Setup)"
    }

    fun testGoogle() {
        if (_isTesting.value) return
        viewModelScope.launch {
            _isTesting.value = true
            try {
                log("--- Google test ---")
                val id = app.settings.googleClientId
                if (id.isBlank()) { log("FAIL: no Client ID saved. Enter it and tap Save Setup."); return@launch }
                val ok = Regex("^\\d+-[a-z0-9]+\\.apps\\.googleusercontent\\.com$").matches(id)
                log(if (ok) "OK: Client ID format" else "FAIL: Client ID format looks wrong: '$id'")

                runCatching { app.youtubeAuthManager.createAuthorizationIntent() }
                    .onSuccess { log("OK: login request built") }
                    .onFailure { log("FAIL: building login request: ${it.javaClass.simpleName}: ${it.message}") }

                val pm = app.packageManager
                val browsers = pm.queryIntentActivities(
                    Intent(Intent.ACTION_VIEW, android.net.Uri.parse("https://accounts.google.com")), 0
                )
                log(if (browsers.isNotEmpty()) "OK: browser found (${browsers.first().activityInfo.packageName})" else "FAIL: no web browser installed (install Chrome)")

                val redirect = "${com.campaignproof.app.BuildConfig.GOOGLE_OAUTH_REDIRECT_SCHEME}:/oauth2redirect"
                val verdict = kotlinx.coroutines.withContext(kotlinx.coroutines.Dispatchers.IO) {
                    runCatching {
                        val url = okhttp3.HttpUrl.Builder().scheme("https").host("accounts.google.com")
                            .addPathSegments("o/oauth2/v2/auth")
                            .addQueryParameter("client_id", id)
                            .addQueryParameter("redirect_uri", redirect)
                            .addQueryParameter("response_type", "code")
                            .addQueryParameter("scope", "https://www.googleapis.com/auth/youtube.readonly")
                            .addQueryParameter("code_challenge", "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM")
                            .addQueryParameter("code_challenge_method", "S256")
                            .build()
                        val client = okhttp3.OkHttpClient.Builder().followRedirects(true).build()
                        client.newCall(okhttp3.Request.Builder().url(url)
                            .header("User-Agent", "Mozilla/5.0 (Linux; Android 14) Mobile").build()).execute().use { r ->
                            val body = r.body?.string().orEmpty()
                            val finalUrl = r.request.url.toString()
                            val all = (finalUrl + " " + body).lowercase()
                            when {
                                "invalid_client" in all || "oauth client was not found" in all -> "FAIL: Google says client not found (invalid_client). Check the ID or that it isn't deleted."
                                "custom uri scheme is not enabled" in all || "custom scheme" in all -> "FAIL: turn ON 'Custom URI scheme' in the Android client's Advanced settings."
                                "redirect_uri_mismatch" in all -> "FAIL: redirect mismatch. Client must be type Android with package com.campaignproof.app."
                                "unauthorized_client" in all || "disabled_client" in all || "deleted_client" in all -> "FAIL: client disabled/unauthorized in Google Cloud."
                                "invalid_request" in all -> "FAIL: Google rejected request (invalid_request) — usually wrong client type (use Android) or custom scheme off."
                                "access_denied" in all || "access_blocked" in all -> "WARN: access blocked — add your Google account as a Test User on the consent screen."
                                r.code in 200..399 -> "OK: Google accepted the Client ID (HTTP ${r.code}). Real login may still need Test Users + SHA-1."
                                else -> "WARN: Google returned HTTP ${r.code}"
                            }
                        }
                    }.getOrElse { "WARN: could not reach Google: ${it.message}" }
                }
                log(verdict)
            } catch (t: Throwable) {
                log("ERROR during test: ${t.javaClass.simpleName}: ${t.message}")
            } finally {
                _isTesting.value = false
            }
        }
    }

    fun testWhop() {
        if (_isTesting.value) return
        viewModelScope.launch {
            _isTesting.value = true
            try {
                log("--- Whop test ---")
                if (app.settings.whopApiKey.isBlank()) { log("FAIL: no Whop API key saved."); return@launch }
                val (code, body) = app.whopApi.testKey()
                log(
                    when (code) {
                        in 200..299 -> "OK: Whop key works (HTTP $code)"
                        401 -> "FAIL: Whop says key invalid (401)"
                        403 -> "FAIL: key valid but missing permission to read bounties (403): $body"
                        else -> "WARN: Whop HTTP $code: $body"
                    }
                )
            } catch (t: Throwable) {
                log("FAIL: could not reach Whop: ${t.message}")
            } finally {
                _isTesting.value = false
            }
        }
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
