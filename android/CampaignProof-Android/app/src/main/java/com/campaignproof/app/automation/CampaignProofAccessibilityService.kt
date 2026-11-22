package com.campaignproof.app.automation

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.content.Intent
import android.graphics.Path
import android.graphics.Rect
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull

data class NavigationTarget(
    val platform: String, // "YOUTUBE" or "INSTAGRAM"
    val expectedAccountName: String,
    val expectedVideoTitle: String,
    val deepLinkUrl: String = ""
)

enum class NavigationStepState {
    IDLE,
    RUNNING,
    DONE,
    MANUAL_FALLBACK_REQUIRED
}

data class AccessibilityNavigationStatus(
    val serviceEnabled: Boolean = false,
    val state: NavigationStepState = NavigationStepState.IDLE,
    val detail: String = "Waiting for recording session",
    val log: List<String> = emptyList()
)

/**
 * Drives the phone while the screen is being recorded:
 * Home screen -> Play Store -> search app -> Open -> find the video -> Analytics -> Audience -> scroll.
 * Finds buttons by their visible text / description and taps them (node click, or a tap
 * gesture on that exact node if the node itself is not clickable).
 */
class CampaignProofAccessibilityService : AccessibilityService() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private var runJob: Job? = null

    override fun onServiceConnected() {
        super.onServiceConnected()
        instance = this
        _status.value = AccessibilityNavigationStatus(serviceEnabled = true, detail = "Automation ready")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) = Unit

    override fun onInterrupt() = Unit

    override fun onDestroy() {
        instance = null
        scope.cancel()
        _status.value = AccessibilityNavigationStatus(serviceEnabled = false, detail = "Automation service off")
        super.onDestroy()
    }

    // ------------------------------------------------------------------ run

    private fun run(target: NavigationTarget, onFinished: (success: Boolean, message: String) -> Unit) {
        runJob?.cancel()
        _status.value = AccessibilityNavigationStatus(true, NavigationStepState.RUNNING, "Starting…", emptyList())
        runJob = scope.launch {
            val result = runCatching {
                if (target.platform == "INSTAGRAM") runInstagram(target) else runYouTube(target)
            }
            val (ok, msg) = result.fold(
                onSuccess = { it },
                onFailure = { false to "Automation error: ${it.message}" }
            )
            step(msg)
            _status.value = _status.value.copy(
                state = if (ok) NavigationStepState.DONE else NavigationStepState.MANUAL_FALLBACK_REQUIRED,
                detail = msg
            )
            onFinished(ok, msg)
        }
    }

    private suspend fun runYouTube(t: NavigationTarget): Pair<Boolean, String> {
        openAppFromHomeViaPlayStore("YouTube Studio", STUDIO_PKG)
        if (!waitForPackage(STUDIO_PKG, 12_000)) return false to "YouTube Studio did not open (is it installed?)"
        delay(3500)

        // Content tab -> find the video
        step("Opening Content tab")
        tapText(listOf("Content"), timeoutMs = 6000)
        delay(2500)

        val titleKey = t.expectedVideoTitle.take(30).trim()
        step("Looking for video: $titleKey")
        var videoNode = findNode { nodeText(it).contains(titleKey, ignoreCase = true) }
        var scrolls = 0
        while (videoNode == null && scrolls < 10) {
            scrollForward()
            delay(1300)
            videoNode = findNode { nodeText(it).contains(titleKey, ignoreCase = true) }
            scrolls++
        }
        if (videoNode != null) {
            tap(videoNode)
            step("Opened video")
            delay(3000)
            step("Opening Analytics")
            val analytics = tapText(listOf("Analytics", "View analytics", "See more", "SEE MORE"), timeoutMs = 7000)
            if (!analytics) step("Analytics button not found, using direct link")
            delay(3000)
        } else {
            step("Video not found in list after $scrolls scrolls, using direct link")
        }

        if (!onAnalyticsScreen() && t.deepLinkUrl.isNotBlank()) {
            openUrl(t.deepLinkUrl, STUDIO_PKG)
            delay(4500)
        }

        step("Opening Audience tab")
        val audience = tapText(listOf("Audience", "AUDIENCE"), timeoutMs = 8000)
        delay(3000)
        if (!audience) step("Audience tab not found — check the recording")

        // Show the geography / demographics cards
        repeat(4) {
            scrollForward()
            delay(2500)
        }
        delay(2000)
        return audience to if (audience) "Done: Audience analytics recorded" else "Finished, but Audience tab was not found"
    }

    private suspend fun runInstagram(t: NavigationTarget): Pair<Boolean, String> {
        openAppFromHomeViaPlayStore("Instagram", IG_PKG)
        if (!waitForPackage(IG_PKG, 12_000)) return false to "Instagram did not open (is it installed?)"
        delay(3000)
        if (t.deepLinkUrl.isNotBlank()) {
            step("Opening the Reel")
            openUrl(t.deepLinkUrl, IG_PKG)
            delay(4000)
        }
        step("Opening insights")
        val insights = tapText(listOf("View insights", "Insights"), timeoutMs = 8000)
        delay(3000)
        repeat(4) {
            scrollForward()
            delay(2500)
        }
        delay(2000)
        return insights to if (insights) "Done: Reel insights recorded" else "Finished, but Insights button was not found"
    }

    /** Home screen -> tap Play Store -> search [appName] -> open its page -> tap Open. */
    private suspend fun openAppFromHomeViaPlayStore(appName: String, pkg: String) {
        step("Going to home screen")
        performGlobalAction(GLOBAL_ACTION_HOME)
        delay(1800)

        step("Opening Play Store")
        val icon = findNode { n ->
            val s = nodeText(n)
            s.equals("Play Store", true) || s.equals("Google Play Store", true) || s.equals("Google Play", true)
        }
        if (icon != null) tap(icon) else launchPackage(PLAY_PKG)
        if (!waitForPackage(PLAY_PKG, 8000)) {
            step("Play Store did not open, opening $appName directly")
            launchPackage(pkg)
            return
        }
        delay(2500)

        step("Searching \"$appName\"")
        tapText(listOf("Search apps & games", "Search for apps & games", "Search apps", "Search"), timeoutMs = 5000)
        delay(1200)
        val field = waitFor(5000) { findNode { it.isEditable } }
        if (field != null) {
            val args = Bundle().apply {
                putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, appName)
            }
            field.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, args)
            delay(1500)
            // Prefer a suggestion row; else press Enter on the keyboard
            val suggestion = findNode { !it.isEditable && nodeText(it).equals(appName, true) }
            if (suggestion != null) {
                tap(suggestion)
            } else if (Build.VERSION.SDK_INT >= 30) {
                field.performAction(AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.id)
            }
            delay(3000)
            // Open the app's page (first result named exactly like the app)
            findNode { !it.isEditable && nodeText(it).startsWith(appName, true) }?.let {
                tap(it)
                delay(2500)
            }
        } else {
            step("Search box not found, opening app page directly")
            openUrl("market://details?id=$pkg", PLAY_PKG)
            delay(3000)
        }

        step("Tapping Open")
        if (!tapText(listOf("Open"), timeoutMs = 7000, exact = true)) {
            openUrl("market://details?id=$pkg", PLAY_PKG)
            delay(3000)
            if (!tapText(listOf("Open"), timeoutMs = 6000, exact = true)) {
                step("Open button not found, launching $appName directly")
                launchPackage(pkg)
            }
        }
    }

    // ------------------------------------------------------------------ helpers

    private fun step(msg: String) {
        val log = (_status.value.log + msg).takeLast(30)
        _status.value = _status.value.copy(detail = msg, log = log)
    }

    private fun roots(): List<AccessibilityNodeInfo> {
        val list = runCatching { windows.mapNotNull { it.root } }.getOrDefault(emptyList())
        return list.ifEmpty { listOfNotNull(rootInActiveWindow) }
    }

    private fun currentPackage(): String? = rootInActiveWindow?.packageName?.toString()

    private fun nodeText(n: AccessibilityNodeInfo): String =
        (n.text?.toString()?.trim()?.ifBlank { null } ?: n.contentDescription?.toString()?.trim()).orEmpty()

    private fun findNode(predicate: (AccessibilityNodeInfo) -> Boolean): AccessibilityNodeInfo? {
        // Only look in the app in front (not our own overlay / notification)
        val front = currentPackage()
        for (root in roots()) {
            if (front != null && root.packageName?.toString() != front) continue
            val queue = ArrayDeque<AccessibilityNodeInfo>()
            queue.add(root)
            var seen = 0
            while (queue.isNotEmpty() && seen < 4000) {
                val n = queue.removeFirst()
                seen++
                if (n.isVisibleToUser && runCatching { predicate(n) }.getOrDefault(false)) return n
                for (i in 0 until n.childCount) n.getChild(i)?.let { queue.add(it) }
            }
        }
        return null
    }

    private suspend fun <T> waitFor(timeoutMs: Long, block: () -> T?): T? =
        withTimeoutOrNull(timeoutMs) {
            var r = block()
            while (r == null) {
                delay(400)
                r = block()
            }
            r
        }

    private suspend fun waitForPackage(pkg: String, timeoutMs: Long): Boolean =
        waitFor(timeoutMs) { if (currentPackage() == pkg) true else null } == true

    private suspend fun tapText(labels: List<String>, timeoutMs: Long, exact: Boolean = false): Boolean {
        val node = waitFor(timeoutMs) {
            findNode { n ->
                val s = nodeText(n)
                s.isNotEmpty() && labels.any { l -> if (exact) s.equals(l, true) else s.equals(l, true) || s.startsWith(l, true) }
            }
        } ?: return false
        return tap(node)
    }

    private suspend fun tap(node: AccessibilityNodeInfo): Boolean {
        var cur: AccessibilityNodeInfo? = node
        var depth = 0
        while (cur != null && depth < 6) {
            if (cur.isClickable && cur.isEnabled && cur.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true
            cur = cur.parent
            depth++
        }
        // Not clickable via accessibility: tap the center of the node on screen
        val r = Rect()
        node.getBoundsInScreen(r)
        if (r.isEmpty) return false
        return gesture(r.exactCenterX(), r.exactCenterY(), r.exactCenterX(), r.exactCenterY(), 60)
    }

    private suspend fun scrollForward() {
        val scrollable = findNode { it.isScrollable }
        if (scrollable?.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD) == true) return
        val dm = resources.displayMetrics
        val x = dm.widthPixels / 2f
        gesture(x, dm.heightPixels * 0.75f, x, dm.heightPixels * 0.35f, 450)
    }

    private suspend fun gesture(x1: Float, y1: Float, x2: Float, y2: Float, durationMs: Long): Boolean {
        val path = Path().apply { moveTo(x1, y1); lineTo(x2, y2) }
        val g = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, durationMs))
            .build()
        val ok = dispatchGesture(g, null, null)
        delay(durationMs + 150)
        return ok
    }

    private fun onAnalyticsScreen(): Boolean =
        findNode { val s = nodeText(it); s.equals("Audience", true) || s.equals("Reach", true) || s.equals("Engagement", true) } != null

    private fun launchPackage(pkg: String) {
        packageManager.getLaunchIntentForPackage(pkg)?.let {
            it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            runCatching { startActivity(it) }
        }
    }

    private fun openUrl(url: String, pkg: String?) {
        val i = Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (pkg != null) i.setPackage(pkg)
        runCatching { startActivity(i) }.onFailure {
            runCatching { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)) }
        }
    }

    fun bringAppToFront() {
        packageManager.getLaunchIntentForPackage(packageName)?.let {
            it.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
            runCatching { startActivity(it) }
        }
    }

    companion object {
        const val STUDIO_PKG = "com.google.android.apps.youtube.creator"
        const val IG_PKG = "com.instagram.android"
        const val PLAY_PKG = "com.android.vending"

        @Volatile private var instance: CampaignProofAccessibilityService? = null

        private val _status = MutableStateFlow(AccessibilityNavigationStatus())
        val status: StateFlow<AccessibilityNavigationStatus> = _status.asStateFlow()

        val isRunning: Boolean get() = instance != null

        /** Starts the automated walk-through. Returns false if the accessibility service is off. */
        fun runAutomation(target: NavigationTarget, onFinished: (Boolean, String) -> Unit): Boolean {
            val svc = instance ?: return false
            svc.run(target, onFinished)
            return true
        }

        fun bringAppToFront() {
            instance?.bringAppToFront()
        }

        fun stop() {
            instance?.runJob?.cancel()
            _status.value = _status.value.copy(state = NavigationStepState.IDLE, detail = "Stopped")
        }

        fun setNavigationTarget(target: NavigationTarget?) {
            if (target == null) stop()
        }
    }
}
