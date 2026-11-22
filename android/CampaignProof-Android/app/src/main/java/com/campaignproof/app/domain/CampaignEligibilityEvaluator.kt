package com.campaignproof.app.domain

import com.campaignproof.app.data.local.CampaignEntity
import com.campaignproof.app.data.local.CampaignPlatform
import com.campaignproof.app.data.local.EligibilityStatus
import com.campaignproof.app.data.local.Platform

data class CountryStat(val countryCode: String, val views: Long, val percentage: Double)
data class DemographicStat(val ageGroup: String, val gender: String, val viewerPercentage: Double)

data class EvaluationResult(
    val targetCountryPercentage: Double?,
    val status: EligibilityStatus,
    val ruleSummary: String
)

/**
 * Evaluates a video against active campaign rules.
 * Strictly distinguishes unavailable data (YELLOW) from failed thresholds (RED)
 * and never invents missing statistics.
 */
object CampaignEligibilityEvaluator {
    fun evaluate(
        platform: Platform,
        title: String,
        publishedAtIso: String,
        isShortOrReel: Boolean,
        viewCount: Long?,
        countryStats: List<CountryStat>,
        demographics: List<DemographicStat>,
        campaign: CampaignEntity
    ): EvaluationResult {
        var anyFail = false
        var anyUnavailable = false
        val reasons = mutableListOf<String>()

        // 1. Platform
        val platformOk = when (campaign.platform) {
            CampaignPlatform.BOTH -> true
            CampaignPlatform.YOUTUBE -> platform == Platform.YOUTUBE
            CampaignPlatform.INSTAGRAM -> platform == Platform.INSTAGRAM
        }
        if (!platformOk) {
            anyFail = true
            reasons.add("Platform ${platform.name} does not match ${campaign.platform.name}")
        }

        // 2. Short-form format
        if (campaign.shortsOrReelsOnly && !isShortOrReel) {
            anyFail = true
            reasons.add("Not a Short/Reel")
        }

        // 3. Publish date
        if (!campaign.publishedAfterIso.isNullOrBlank()) {
            val videoDate = publishedAtIso.take(10)
            if (videoDate.length < 10) {
                anyUnavailable = true
                reasons.add("Publish date unavailable")
            } else if (videoDate < campaign.publishedAfterIso) {
                anyFail = true
                reasons.add("Published $videoDate (before ${campaign.publishedAfterIso})")
            }
        }

        // 4. Keyword
        if (!campaign.requiredKeyword.isNullOrBlank()) {
            if (!title.contains(campaign.requiredKeyword, ignoreCase = true)) {
                anyFail = true
                reasons.add("Missing keyword \"${campaign.requiredKeyword}\"")
            }
        }

        // 5. Minimum views
        if (viewCount == null) {
            anyUnavailable = true
            reasons.add("View count unavailable from API")
        } else if (viewCount < campaign.minViews) {
            anyFail = true
            reasons.add("Views $viewCount < min ${campaign.minViews}")
        }

        // 6. Target country %
        val targetCountryPct = if (countryStats.isNotEmpty()) {
            countryStats.firstOrNull {
                it.countryCode.equals(campaign.targetCountryCode, ignoreCase = true)
            }?.percentage ?: 0.0
        } else {
            null
        }

        if (campaign.minCountryPercentage > 0.0) {
            if (targetCountryPct == null) {
                anyUnavailable = true
                reasons.add("${campaign.targetCountryCode} audience % unavailable")
            } else if (targetCountryPct < campaign.minCountryPercentage) {
                anyFail = true
                reasons.add(
                    "${campaign.targetCountryCode} ${"%.1f".format(targetCountryPct)}% < min ${campaign.minCountryPercentage}%"
                )
            }
        }

        // 7. Optional age demographics
        val targetAges = campaign.requiredAgeGroupsCsv
            .split(",")
            .map { it.trim().removePrefix("age") }
            .filter { it.isNotEmpty() }
        if (targetAges.isNotEmpty() && (campaign.minAgeGroupPercentage ?: 0.0) > 0.0) {
            if (demographics.isEmpty()) {
                anyUnavailable = true
                reasons.add("Age demographics unavailable")
            } else {
                val sumPct = demographics
                    .filter { d -> targetAges.contains(d.ageGroup.removePrefix("age")) }
                    .sumOf { it.viewerPercentage }
                if (sumPct < campaign.minAgeGroupPercentage!!) {
                    anyFail = true
                    reasons.add("Age target ${"%.1f".format(sumPct)}% < ${campaign.minAgeGroupPercentage}%")
                }
            }
        }

        // 8. Optional gender demographic
        if (campaign.requiredGender != "ANY" && (campaign.minGenderPercentage ?: 0.0) > 0.0) {
            if (demographics.isEmpty()) {
                anyUnavailable = true
                reasons.add("Gender demographics unavailable")
            } else {
                val sumPct = demographics
                    .filter { it.gender.equals(campaign.requiredGender, ignoreCase = true) }
                    .sumOf { it.viewerPercentage }
                if (sumPct < campaign.minGenderPercentage!!) {
                    anyFail = true
                    reasons.add("${campaign.requiredGender} ${"%.1f".format(sumPct)}% < ${campaign.minGenderPercentage}%")
                }
            }
        }

        val status = when {
            anyFail -> EligibilityStatus.NOT_ELIGIBLE
            anyUnavailable -> EligibilityStatus.INSUFFICIENT_DATA
            else -> EligibilityStatus.ELIGIBLE
        }

        val summary = if (reasons.isEmpty()) {
            "Meets all campaign requirements"
        } else {
            reasons.joinToString(" · ")
        }

        return EvaluationResult(targetCountryPct, status, summary)
    }
}
