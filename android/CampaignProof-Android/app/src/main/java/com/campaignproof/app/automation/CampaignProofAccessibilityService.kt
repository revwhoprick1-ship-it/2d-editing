package com.campaignproof.app.automation

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class NavigationTarget(
    val platform: String, // "YOUTUBE" or "INSTAGRAM"
    val expectedAccountName: String,
    val expectedVideoTitle: String
)

enum class NavigationStepState {
    IDLE,
    SEARCHING_VIDEO,
    OPENING_ANALYTICS,
    OPENING_AUDIENCE_TAB,
    AUDIENCE_VISIBLE_AWAITING_CONFIRMATION,
    MANUAL_FALLBACK_REQUIRED
}

data class AccessibilityNavigationStatus(
    val serviceEnabled: Boolean = false,
    val state: NavigationStepState = NavigationStepState.IDLE,
    val detail: String = "Waiting for recording session"
)

/**
 * Deterministic, user-authorized AccessibilityService.
 * - Uses semantic text & node hierarchy traversal (NEVER blind coordinate taps).
 * - Never bypasses login screens or security dialogs.
 * - Stops immediately into MANUAL_FALLBACK_REQUIRED if an expected element or title is missing,
 *   guaranteeing CampaignProof never silently records the wrong video.
 */
class CampaignProofAccessibilityService : AccessibilityService() {

    override fun onServiceConnected() {
        super.onServiceConnected()
        _status.value = AccessibilityNavigationStatus(
            serviceEnabled = true,
            state = NavigationStepState.IDLE,
            detail = "Navigation assistant ready"
        )
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val target = activeTarget ?: return
        val root = rootInActiveWindow ?: return

        try {
            if (target.platform == "YOUTUBE") {
                handleYouTubeStudioNavigation(root, target)
            } else {
                handleInstagramNavigation(root, target)
            }
        } catch (e: Exception) {
            _status.value = AccessibilityNavigationStatus(
                serviceEnabled = true,
                state = NavigationStepState.MANUAL_FALLBACK_REQUIRED,
                detail = "Paused for manual step: ${e.message}"
            )
        }
    }

    private fun handleYouTubeStudioNavigation(
        root: AccessibilityNodeInfo,
        target: NavigationTarget
    ) {
        // 1. Check if we are already on the Audience demographics section
        val hasGeographies = hasTextNode(root, "Top geographies") || hasTextNode(root, "Geographies")
        val hasAudienceTab = hasTextNode(root, "Audience")
        val hasAgeOrGender = hasTextNode(root, "Age") || hasTextNode(root, "Gender")

        if (hasGeographies || (hasAudienceTab && hasAgeOrGender)) {
            _status.value = AccessibilityNavigationStatus(
                serviceEnabled = true,
                state = NavigationStepState.AUDIENCE_VISIBLE_AWAITING_CONFIRMATION,
                detail = "Audience demographics detected. Verify account (${target.expectedAccountName}) and tap Confirm & Record."
            )
            return
        }

        // 2. If "Audience" tab is visible on Video Analytics, click it deterministically
        if (clickClickableNodeByText(root, "Audience")) {
            _status.value = AccessibilityNavigationStatus(
                serviceEnabled = true,
                state = NavigationStepState.OPENING_AUDIENCE_TAB,
                detail = "Selected Audience tab in YouTube Studio"
            )
            return
        }

        // 3. If "Analytics" or "Go to video analytics" is visible, verify expected video title first
        val titlePrefix = target.expectedVideoTitle.take(28)
        if (hasTextNode(root, titlePrefix)) {
            if (clickClickableNodeByText(root, "Go to video analytics") ||
                clickClickableNodeByText(root, "Analytics")
            ) {
                _status.value = AccessibilityNavigationStatus(
                    serviceEnabled = true,
                    state = NavigationStepState.OPENING_ANALYTICS,
                    detail = "Matched video title; opening Analytics"
                )
                return
            }
        }

        // 4. Otherwise do NOT blindly click; alert user to complete step manually
        _status.value = AccessibilityNavigationStatus(
            serviceEnabled = true,
            state = NavigationStepState.MANUAL_FALLBACK_REQUIRED,
            detail = "Navigate to \"${target.expectedVideoTitle}\" -> Analytics -> Audience, then confirm."
        )
    }

    private fun handleInstagramNavigation(
        root: AccessibilityNodeInfo,
        target: NavigationTarget
    ) {
        if (hasTextNode(root, "Top countries") || hasTextNode(root, "Top locations") || hasTextNode(root, "Audience")) {
            _status.value = AccessibilityNavigationStatus(
                serviceEnabled = true,
                state = NavigationStepState.AUDIENCE_VISIBLE_AWAITING_CONFIRMATION,
                detail = "Instagram Audience insights visible. Confirm account (${target.expectedAccountName}) before recording."
            )
            return
        }

        if (clickClickableNodeByText(root, "View insights") || clickClickableNodeByText(root, "Insights")) {
            _status.value = AccessibilityNavigationStatus(
                serviceEnabled = true,
                state = NavigationStepState.OPENING_ANALYTICS,
                detail = "Opened Instagram Reel Insights"
            )
            return
        }

        _status.value = AccessibilityNavigationStatus(
            serviceEnabled = true,
            state = NavigationStepState.MANUAL_FALLBACK_REQUIRED,
            detail = "Open Reel Insights -> Audience in Instagram, then confirm to start recording."
        )
    }

    private fun hasTextNode(root: AccessibilityNodeInfo, query: String): Boolean {
        if (query.isBlank()) return false
        return root.findAccessibilityNodeInfosByText(query).isNotEmpty()
    }

    private fun clickClickableNodeByText(root: AccessibilityNodeInfo, label: String): Boolean {
        val nodes = root.findAccessibilityNodeInfosByText(label)
        for (node in nodes) {
            var current: AccessibilityNodeInfo? = node
            while (current != null) {
                if (current.isClickable && current.isEnabled) {
                    return current.performAction(AccessibilityNodeInfo.ACTION_CLICK)
                }
                current = current.parent
            }
        }
        return false
    }

    override fun onInterrupt() {
        _status.value = _status.value.copy(
            state = NavigationStepState.MANUAL_FALLBACK_REQUIRED,
            detail = "Accessibility service interrupted; manual completion active."
        )
    }

    override fun onDestroy() {
        super.onDestroy()
        _status.value = AccessibilityNavigationStatus(serviceEnabled = false)
    }

    companion object {
        @Volatile private var activeTarget: NavigationTarget? = null

        private val _status = MutableStateFlow(AccessibilityNavigationStatus())
        val status: StateFlow<AccessibilityNavigationStatus> = _status.asStateFlow()

        fun setNavigationTarget(target: NavigationTarget?) {
            activeTarget = target
            if (target == null) {
                _status.value = _status.value.copy(
                    state = NavigationStepState.IDLE,
                    detail = "Idle"
                )
            } else {
                _status.value = _status.value.copy(
                    state = NavigationStepState.SEARCHING_VIDEO,
                    detail = "Looking for \"${target.expectedVideoTitle}\""
                )
            }
        }
    }
}
