package com.campaignproof.app.automation

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.campaignproof.app.data.local.Platform
import com.campaignproof.app.data.local.ScannedVideoEntity

/**
 * Launches YouTube Studio or Instagram using official Android Intents first,
 * falling back cleanly to HTTPS deep links if the native app is unavailable.
 */
object StudioNavigationLauncher {
    private const val YT_STUDIO_PACKAGE = "com.google.android.apps.youtube.creator"
    private const val INSTAGRAM_PACKAGE = "com.instagram.android"

    fun openVideoAnalytics(context: Context, video: ScannedVideoEntity): Result<String> {
        return when (video.platform) {
            Platform.YOUTUBE -> openYouTubeStudio(context, video)
            Platform.INSTAGRAM -> openInstagramReel(context, video)
        }
    }

    private fun openYouTubeStudio(context: Context, video: ScannedVideoEntity): Result<String> {
        val studioUri = Uri.parse(video.studioAnalyticsUrl)
        val studioIntent = Intent(Intent.ACTION_VIEW, studioUri).apply {
            setPackage(YT_STUDIO_PACKAGE)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        return runCatching {
            if (studioIntent.resolveActivity(context.packageManager) != null) {
                context.startActivity(studioIntent)
                "Opened YouTube Studio app for \"${video.title}\""
            } else {
                // Fallback to YouTube Studio launch intent or mobile web Studio
                val launch = context.packageManager.getLaunchIntentForPackage(YT_STUDIO_PACKAGE)
                if (launch != null) {
                    launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(launch)
                    "Opened YouTube Studio home. Navigate to \"${video.title}\" -> Analytics -> Audience."
                } else {
                    val webIntent = Intent(Intent.ACTION_VIEW, studioUri).apply {
                        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    }
                    context.startActivity(webIntent)
                    "YouTube Studio app not installed; opened Studio web analytics."
                }
            }
        }
    }

    private fun openInstagramReel(context: Context, video: ScannedVideoEntity): Result<String> {
        val reelUri = Uri.parse(video.videoUrl)
        val igIntent = Intent(Intent.ACTION_VIEW, reelUri).apply {
            setPackage(INSTAGRAM_PACKAGE)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        return runCatching {
            if (igIntent.resolveActivity(context.packageManager) != null) {
                context.startActivity(igIntent)
                "Opened Instagram Reel. Tap View Insights -> Audience and confirm visibility."
            } else {
                val webIntent = Intent(Intent.ACTION_VIEW, reelUri).apply {
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                context.startActivity(webIntent)
                "Instagram app not installed; opened Reel in browser."
            }
        }
    }
}
