package com.campaignproof.app.domain

import com.campaignproof.app.data.local.AccountEntity
import com.campaignproof.app.data.local.AuthMode
import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.CampaignProofDatabase
import com.campaignproof.app.data.local.Platform
import com.campaignproof.app.data.local.ScannedVideoEntity
import com.campaignproof.app.data.local.SecureTokenStore
import com.campaignproof.app.data.local.TokenStatus
import com.campaignproof.app.data.remote.ApiClientFactory
import com.campaignproof.app.data.remote.YouTubeAuthManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.LocalDate

data class AccountScanResult(
    val accountName: String,
    val platform: Platform,
    val videosFound: Int,
    val error: String? = null
)

class VideoScannerRepository(
    private val db: CampaignProofDatabase,
    private val tokenStore: SecureTokenStore,
    private val youtubeAuthManager: YouTubeAuthManager
) {
    suspend fun scanAllSelectedAccounts(campaign: CampaignEntity): List<AccountScanResult> =
        withContext(Dispatchers.IO) {
            val selected = db.accountDao().getSelectedForScan()
            val results = mutableListOf<AccountScanResult>()

            for (account in selected) {
                when (account.platform) {
                    Platform.YOUTUBE -> results.add(scanYouTubeChannel(account, campaign))
                    Platform.INSTAGRAM -> results.add(scanInstagramAccount(account, campaign))
                }
            }
            results
        }

    private suspend fun scanYouTubeChannel(
        account: AccountEntity,
        campaign: CampaignEntity
    ): AccountScanResult {
        var bundle = tokenStore.getTokens(account.id)
            ?: return markExpired(account, "Missing OAuth token. Reconnect YouTube channel.")

        if (System.currentTimeMillis() >= bundle.expiresAtEpochMs - 60_000L) {
            val refresh = bundle.refreshToken
                ?: return markExpired(account, "Token expired with no refresh token.")
            try {
                bundle = youtubeAuthManager.refreshAccessToken(refresh)
                tokenStore.saveTokens(account.id, bundle)
            } catch (e: Exception) {
                return markExpired(account, e.message ?: "Token refresh failed")
            }
        }

        val bearer = "Bearer ${bundle.accessToken}"
        return try {
            val uploadsId = account.uploadsPlaylistId
                ?: ApiClientFactory.youtubeDataApi.getMyChannels(bearer)
                    .items.firstOrNull { it.id == account.externalId }
                    ?.contentDetails?.relatedPlaylists?.uploads
                ?: return AccountScanResult(account.name, Platform.YOUTUBE, 0, "Uploads playlist not found")

            val playlistItems = ApiClientFactory.youtubeDataApi
                .getPlaylistItems(bearer, playlistId = uploadsId)
                .items.mapNotNull { it.contentDetails?.videoId }

            if (playlistItems.isEmpty()) {
                return AccountScanResult(account.name, Platform.YOUTUBE, 0)
            }

            val videoDetails = ApiClientFactory.youtubeDataApi
                .getVideos(bearer, idsCsv = playlistItems.take(50).joinToString(","))
                .items

            val todayIso = LocalDate.now().toString()
            val scanned = mutableListOf<ScannedVideoEntity>()

            for (v in videoDetails) {
                val durationSec = parseIsoDuration(v.contentDetails?.duration)
                val isShort = durationSec != null && durationSec <= 180
                val views = v.statistics?.viewCount?.toLongOrNull()
                val publishedAt = v.snippet?.publishedAt ?: todayIso
                val startDate = publishedAt.take(10).ifBlank { "2020-01-01" }

                val countryStats = mutableListOf<CountryStat>()
                val demographics = mutableListOf<DemographicStat>()
                val notes = mutableListOf<String>()

                if (views == null || views >= campaign.minViews) {
                    // Geography breakdown
                    runCatching {
                        ApiClientFactory.youtubeAnalyticsApi.queryReport(
                            authHeader = bearer,
                            startDate = startDate,
                            endDate = todayIso,
                            metrics = "views",
                            dimensions = "country",
                            filters = "video==${v.id}",
                            sort = "-views"
                        )
                    }.onSuccess { resp ->
                        val rows = resp.rows.orEmpty()
                        val total = rows.sumOf { (it.getOrNull(1) as? Number)?.toLong() ?: 0L }
                        if (total > 0L) {
                            rows.forEach { row ->
                                val code = row.getOrNull(0)?.toString()?.uppercase() ?: return@forEach
                                val cViews = (row.getOrNull(1) as? Number)?.toLong() ?: 0L
                                countryStats.add(CountryStat(code, cViews, (cViews * 100.0) / total))
                            }
                        } else {
                            notes.add("YouTube Analytics returned no country data (privacy threshold or delay).")
                        }
                    }.onFailure { err ->
                        notes.add("Country analytics error: ${err.message}")
                    }

                    // Age & gender breakdown
                    runCatching {
                        ApiClientFactory.youtubeAnalyticsApi.queryReport(
                            authHeader = bearer,
                            startDate = startDate,
                            endDate = todayIso,
                            metrics = "viewerPercentage",
                            dimensions = "ageGroup,gender",
                            filters = "video==${v.id}"
                        )
                    }.onSuccess { resp ->
                        resp.rows.orEmpty().forEach { row ->
                            val age = row.getOrNull(0)?.toString()?.removePrefix("age") ?: return@forEach
                            val gender = row.getOrNull(1)?.toString() ?: "unknown"
                            val pct = (row.getOrNull(2) as? Number)?.toDouble() ?: 0.0
                            demographics.add(DemographicStat(age, gender, pct))
                        }
                        if (demographics.isEmpty()) {
                            notes.add("Age/gender demographics suppressed by YouTube privacy thresholds.")
                        }
                    }.onFailure { err ->
                        notes.add("Demographic analytics error: ${err.message}")
                    }
                } else {
                    notes.add("Skipped analytics query because view count is below campaign minimum.")
                }

                val eval = CampaignEligibilityEvaluator.evaluate(
                    platform = Platform.YOUTUBE,
                    title = v.snippet?.title ?: "Untitled Video",
                    publishedAtIso = publishedAt,
                    isShortOrReel = isShort,
                    viewCount = views,
                    countryStats = countryStats,
                    demographics = demographics,
                    campaign = campaign
                )

                scanned.add(
                    ScannedVideoEntity(
                        id = "yt_${account.id}_${v.id}",
                        externalVideoId = v.id,
                        accountId = account.id,
                        accountName = account.name,
                        accountHandle = account.handle,
                        platform = Platform.YOUTUBE,
                        title = v.snippet?.title ?: "Untitled Video",
                        videoUrl = if (isShort) "https://www.youtube.com/shorts/${v.id}" else "https://www.youtube.com/watch?v=${v.id}",
                        studioAnalyticsUrl = "https://studio.youtube.com/video/${v.id}/analytics/tab-audience/period-default",
                        thumbnailUrl = v.snippet?.thumbnails?.high?.url ?: v.snippet?.thumbnails?.medium?.url,
                        publishedAtIso = publishedAt,
                        durationSeconds = durationSec,
                        isShortOrReel = isShort,
                        viewCount = views,
                        targetCountryCode = campaign.targetCountryCode,
                        targetCountryPercentage = eval.targetCountryPercentage,
                        countryBreakdownJson = countryStats.joinToString(";") { "${it.countryCode}:${"%.1f".format(it.percentage)}" },
                        demographicsJson = demographics.joinToString(";") { "${it.ageGroup}/${it.gender}:${"%.1f".format(it.viewerPercentage)}" },
                        demographicsAvailable = demographics.isNotEmpty(),
                        dataAvailabilityNotesJson = notes.joinToString(" | "),
                        campaignId = campaign.id,
                        eligibilityStatus = eval.status,
                        ruleSummary = eval.ruleSummary,
                        scannedAtEpochMs = System.currentTimeMillis()
                    )
                )
            }

            db.scannedVideoDao().deleteByAccount(account.id)
            db.scannedVideoDao().upsertAll(scanned)
            db.accountDao().upsert(account.copy(tokenStatus = TokenStatus.ACTIVE, lastError = null, lastScannedAtEpochMs = System.currentTimeMillis()))
            AccountScanResult(account.name, Platform.YOUTUBE, scanned.size)
        } catch (e: Exception) {
            db.accountDao().updateTokenStatus(account.id, TokenStatus.ERROR, e.message)
            AccountScanResult(account.name, Platform.YOUTUBE, 0, e.message)
        }
    }

    private suspend fun scanInstagramAccount(
        account: AccountEntity,
        campaign: CampaignEntity
    ): AccountScanResult {
        if (account.authMode == AuthMode.MANUAL_FALLBACK) {
            val existing = db.scannedVideoDao().getByAccount(account.id)
            return AccountScanResult(account.name, Platform.INSTAGRAM, existing.size)
        }

        val token = tokenStore.getTokens(account.id)?.accessToken
            ?: return markExpired(account, "Meta token missing or expired.")

        return try {
            val media = ApiClientFactory.metaGraphApi.getMediaList(account.externalId, accessToken = token).data
            val reels = media.filter { it.media_product_type == "REELS" || it.media_type == "VIDEO" }
            val scanned = mutableListOf<ScannedVideoEntity>()

            for (item in reels) {
                val views = runCatching {
                    ApiClientFactory.metaGraphApi.getMediaInsights(item.id, accessToken = token)
                        .data.firstOrNull { it.name == "views" }?.values?.firstOrNull()?.value
                }.getOrNull()

                val title = item.caption?.lineSequence()?.firstOrNull()?.take(110) ?: "Instagram Reel ${item.id.takeLast(6)}"
                val eval = CampaignEligibilityEvaluator.evaluate(
                    platform = Platform.INSTAGRAM,
                    title = title,
                    publishedAtIso = item.timestamp ?: "",
                    isShortOrReel = true,
                    viewCount = views,
                    countryStats = emptyList(), // Meta API does not expose per-Reel country stats
                    demographics = emptyList(),
                    campaign = campaign
                )

                scanned.add(
                    ScannedVideoEntity(
                        id = "ig_${account.id}_${item.id}",
                        externalVideoId = item.id,
                        accountId = account.id,
                        accountName = account.name,
                        accountHandle = account.handle,
                        platform = Platform.INSTAGRAM,
                        title = title,
                        videoUrl = item.permalink ?: "https://www.instagram.com/reel/${item.id}/",
                        studioAnalyticsUrl = item.permalink ?: "https://www.instagram.com/reel/${item.id}/",
                        thumbnailUrl = item.thumbnail_url,
                        publishedAtIso = item.timestamp ?: "",
                        durationSeconds = null,
                        isShortOrReel = true,
                        viewCount = views,
                        targetCountryCode = campaign.targetCountryCode,
                        targetCountryPercentage = null,
                        countryBreakdownJson = "",
                        demographicsJson = "",
                        demographicsAvailable = false,
                        dataAvailabilityNotesJson = "Meta Graph API does not expose per-Reel country breakdown; verify manually in Instagram Insights.",
                        campaignId = campaign.id,
                        eligibilityStatus = eval.status,
                        ruleSummary = eval.ruleSummary,
                        scannedAtEpochMs = System.currentTimeMillis()
                    )
                )
            }

            db.scannedVideoDao().deleteByAccount(account.id)
            db.scannedVideoDao().upsertAll(scanned)
            db.accountDao().upsert(account.copy(tokenStatus = TokenStatus.ACTIVE, lastError = null, lastScannedAtEpochMs = System.currentTimeMillis()))
            AccountScanResult(account.name, Platform.INSTAGRAM, scanned.size)
        } catch (e: Exception) {
            db.accountDao().updateTokenStatus(account.id, TokenStatus.ERROR, e.message)
            AccountScanResult(account.name, Platform.INSTAGRAM, 0, e.message)
        }
    }

    private suspend fun markExpired(account: AccountEntity, reason: String): AccountScanResult {
        db.accountDao().updateTokenStatus(account.id, TokenStatus.TOKEN_EXPIRED, reason)
        return AccountScanResult(account.name, account.platform, 0, reason)
    }

    private fun parseIsoDuration(iso: String?): Int? {
        if (iso == null) return null
        val match = Regex("^PT(?:(\\d+)H)?(?:(\\d+)M)?(?:(\\d+)S)?$", RegexOption.IGNORE_CASE).matchEntire(iso)
            ?: return null
        val h = match.groupValues[1].toIntOrNull() ?: 0
        val m = match.groupValues[2].toIntOrNull() ?: 0
        val s = match.groupValues[3].toIntOrNull() ?: 0
        return h * 3600 + m * 60 + s
    }
}
