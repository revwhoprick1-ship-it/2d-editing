package com.campaignproof.app

import android.app.Activity
import android.content.Context
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.sp
import com.campaignproof.app.automation.CampaignProofAccessibilityService
import com.campaignproof.app.data.local.EligibilityStatus
import com.campaignproof.app.ui.screens.AccountsScreen
import com.campaignproof.app.ui.screens.CampaignsScreen
import com.campaignproof.app.ui.screens.DashboardScreen
import com.campaignproof.app.ui.screens.EligibleVideosScreen
import com.campaignproof.app.ui.screens.RecordingWorkflowScreen
import com.campaignproof.app.ui.screens.RecordingsLibraryScreen
import com.campaignproof.app.ui.screens.SetupScreen
import com.campaignproof.app.ui.theme.CampaignProofTheme
import com.campaignproof.app.ui.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    private val googleOAuthLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val data = result.data
        if (data != null) viewModel.handleGoogleOAuthIntentResult(data)
        else viewModel.showBanner("Google login cancelled or closed.")
    }

    private val mediaProjectionLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK && result.data != null) {
            viewModel.confirmEvidenceAndStartCapture(result.resultCode, result.data!!)
        } else {
            viewModel.showBanner("Screen recording not allowed — tap Start again.")
        }
    }

    private fun requestScreenCapture() {
        val mgr = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        val intent = if (android.os.Build.VERSION.SDK_INT >= 34) {
            // Force "entire screen" so Home / Play Store / Studio are all captured
            mgr.createScreenCaptureIntent(android.media.projection.MediaProjectionConfig.createConfigForDefaultDisplay())
        } else {
            mgr.createScreenCaptureIntent()
        }
        mediaProjectionLauncher.launch(intent)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val app = application as CampaignProofApplication

        setContent {
            CampaignProofTheme {
                val accounts by viewModel.accounts.collectAsState()
                val campaigns by viewModel.campaigns.collectAsState()
                val videos by viewModel.videos.collectAsState()
                val recordings by viewModel.recordings.collectAsState()
                val session by viewModel.workflowSession.collectAsState()
                val recorderState by viewModel.recorderState.collectAsState()
                val isScanning by viewModel.isScanning.collectAsState()
                val banner by viewModel.statusBanner.collectAsState()
                val accStatus by CampaignProofAccessibilityService.status.collectAsState()
                val settings by viewModel.settings.collectAsState()
                val whopImport by viewModel.whopImport.collectAsState()
                val testLog by viewModel.testLog.collectAsState()
                val isTesting by viewModel.isTesting.collectAsState()

                var activeTab by remember { mutableStateOf("dashboard") }
                val snackbarHostState = remember { SnackbarHostState() }

                // As soon as a session is queued: check automation is on, then ask Android to record.
                LaunchedEffect(session.pendingAutoStart) {
                    if (session.pendingAutoStart) {
                        viewModel.consumeAutoStart()
                        activeTab = "record"
                        if (!CampaignProofAccessibilityService.isRunning) {
                            viewModel.showBanner("Turn ON CampaignProof in Accessibility, then press Start again.")
                            runCatching {
                                startActivity(android.content.Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS))
                            }
                        } else if (recorderState == com.campaignproof.app.recording.RecorderState.IDLE) {
                            requestScreenCapture()
                        }
                    }
                }

                LaunchedEffect(banner) {
                    if (!banner.isNullOrBlank()) {
                        snackbarHostState.showSnackbar(banner!!)
                        viewModel.clearBanner()
                    }
                }

                Scaffold(
                    snackbarHost = { SnackbarHost(snackbarHostState) },
                    bottomBar = {
                        NavigationBar {
                            listOf(
                                "dashboard" to "Home",
                                "accounts" to "Accounts",
                                "campaigns" to "Rules",
                                "videos" to "Videos",
                                "record" to "Record",
                                "library" to "Library",
                                "setup" to "Setup"
                            ).forEach { (key, label) ->
                                NavigationBarItem(
                                    selected = activeTab == key,
                                    onClick = { activeTab = key },
                                    icon = { Text(label.take(1)) },
                                    label = { Text(label, maxLines = 1, fontSize = 10.sp) }
                                )
                            }
                        }
                    }
                ) { padding ->
                    Box(modifier = Modifier.padding(padding)) {
                        when (activeTab) {
                            "dashboard" -> DashboardScreen(
                                accounts = accounts,
                                activeCampaign = campaigns.firstOrNull { it.isActive },
                                videos = videos,
                                recordings = recordings,
                                isScanning = isScanning,
                                onScanAccounts = viewModel::scanAccounts,
                                onStartRecording = {
                                    val eligible = videos.filter { it.eligibilityStatus == EligibilityStatus.ELIGIBLE }
                                    if (eligible.isNotEmpty()) {
                                        viewModel.startRecordingSession(eligible)
                                        activeTab = "record"
                                    }
                                },
                                onNavigateToAccounts = { activeTab = "accounts" },
                                onTestRecording = { if (viewModel.startTestRecording()) activeTab = "record" }
                            )
                            "accounts" -> AccountsScreen(
                                accounts = accounts,
                                onConnectYouTube = {
                                    if (app.youtubeAuthManager.isConfigured()) {
                                        try {
                                            googleOAuthLauncher.launch(app.youtubeAuthManager.createAuthorizationIntent())
                                        } catch (t: Throwable) {
                                            viewModel.reportError("Connect YouTube", t)
                                            activeTab = "setup"
                                        }
                                    } else {
                                        viewModel.showBanner("Enter your Google OAuth Client ID in Setup first.")
                                        activeTab = "setup"
                                    }
                                },
                                onAddManualInstagram = viewModel::addManualInstagramAccount,
                                onToggleAccount = viewModel::toggleAccountSelection,
                                onRemoveAccount = viewModel::removeAccount
                            )
                            "campaigns" -> CampaignsScreen(
                                campaigns = campaigns,
                                onSaveCampaign = viewModel::saveCampaign,
                                onActivateCampaign = viewModel::activateCampaign,
                                whopImport = whopImport,
                                onLookupWhop = viewModel::lookupWhop,
                                onClearWhop = viewModel::clearWhopImport
                            )
                            "videos" -> EligibleVideosScreen(
                                videos = videos,
                                onStartRecordingQueue = { queue ->
                                    viewModel.startRecordingSession(queue)
                                    activeTab = "record"
                                },
                                onTestRecording = { if (viewModel.startTestRecording()) activeTab = "record" }
                            )
                            "record" -> RecordingWorkflowScreen(
                                session = session,
                                recorderState = recorderState,
                                accessibilityStatus = accStatus,
                                onRequestMediaProjectionAndStart = {
                                    if (!CampaignProofAccessibilityService.isRunning) {
                                        viewModel.showBanner("Turn ON CampaignProof in Accessibility first.")
                                        runCatching { startActivity(android.content.Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
                                    } else requestScreenCapture()
                                },
                                onPause = viewModel::pauseRecording,
                                onResume = viewModel::resumeRecording,
                                onStop = viewModel::stopRecording,
                                onSkip = viewModel::skipVideo,
                                onRetryNavigation = viewModel::retryNavigation,
                                onCancel = viewModel::cancelRecording
                            )
                            "library" -> RecordingsLibraryScreen(
                                recordings = recordings,
                                onDeleteRecording = viewModel::deleteRecording
                            )
                            "setup" -> SetupScreen(
                                current = settings,
                                onSave = viewModel::saveSettings,
                                testLog = testLog,
                                isTesting = isTesting,
                                onTestGoogle = viewModel::testGoogle,
                                onTestWhop = viewModel::testWhop,
                                onClearLog = viewModel::clearTestLog
                            )
                        }
                    }
                }
            }
        }
    }
}
