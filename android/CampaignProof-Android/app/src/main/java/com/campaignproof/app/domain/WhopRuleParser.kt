package com.campaignproof.app.domain

import com.campaignproof.app.data.local.CampaignPlatform

/** Rule values found in a Whop campaign's text. Null = not found (user must fill it in). */
data class ParsedWhopRules(
    val minViews: Long?,
    val countryCode: String?,
    val minCountryPercentage: Double?,
    val platform: CampaignPlatform?,
    val shortsOnly: Boolean?,
    val notes: List<String>
)

/**
 * Whop campaigns write their rules as free text in the description. This pulls out the common
 * ones (min views, country %, platforms) as SUGGESTIONS. Anything not clearly stated stays null.
 */
object WhopRuleParser {
    private val COUNTRIES = linkedMapOf(
        "US" to listOf("united states", "usa", "u.s.", "us", "american"),
        "GB" to listOf("united kingdom", "uk", "britain"),
        "CA" to listOf("canada", "canadian"),
        "AU" to listOf("australia", "australian"),
        "DE" to listOf("germany", "german"),
        "FR" to listOf("france", "french"),
        "BR" to listOf("brazil", "brazilian"),
        "IN" to listOf("india", "indian"),
        "PH" to listOf("philippines", "filipino")
    )

    fun parse(text: String, extraFields: List<Pair<String, String>> = emptyList()): ParsedWhopRules {
        val all = buildString {
            append(text)
            extraFields.forEach { (k, v) -> append("\n").append(k).append(": ").append(v) }
        }
        val lower = all.lowercase()
        val notes = mutableListOf<String>()

        // --- Minimum views ---
        val viewPatterns = listOf(
            Regex("(?:min(?:imum)?\\.?|at least|over|>=?)\\s*(?:of\\s*)?([\\d.,]+)\\s*([km]?)\\s*\\+?\\s*views"),
            Regex("([\\d.,]+)\\s*([km]?)\\s*\\+?\\s*views?\\s*(?:min(?:imum)?|required|needed|to (?:get paid|qualify))")
        )
        val minViews = viewPatterns.firstNotNullOfOrNull { r ->
            r.find(lower)?.let { m -> toNumber(m.groupValues[1], m.groupValues[2]) }
        }
        if (minViews != null) notes.add("Min views from text: $minViews")

        // --- Country percentage, e.g. "50% US", "US audience 60%", "at least 70% of views from the United States"
        var countryCode: String? = null
        var countryPct: Double? = null
        loop@ for ((code, names) in COUNTRIES) {
            for (n in names) {
                val name = Regex.escape(n)
                val before = Regex("(\\d{1,3}(?:\\.\\d+)?)\\s*%[^.\\n%]{0,40}?\\b$name\\b")
                val after = Regex("\\b$name\\b[^.\\n%]{0,40}?(\\d{1,3}(?:\\.\\d+)?)\\s*%")
                val m = before.find(lower) ?: after.find(lower)
                if (m != null) {
                    countryCode = code
                    countryPct = m.groupValues[1].toDoubleOrNull()
                    break@loop
                }
            }
        }
        if (countryCode == null) {
            // Country mentioned without a % (e.g. "US viewers only")
            for ((code, names) in COUNTRIES) {
                if (names.filter { it.length > 2 }.any { Regex("\\b${Regex.escape(it)}\\b").containsMatchIn(lower) } ||
                    Regex("\\b(us|usa)\\s+(only|viewers|audience|views)").containsMatchIn(lower) && code == "US"
                ) {
                    countryCode = code
                    notes.add("Country $code mentioned but no % found — set it yourself")
                    break
                }
            }
        } else {
            notes.add("Country rule from text: $countryCode >= $countryPct%")
        }
        if (Regex("\\btier\\s*1\\b").containsMatchIn(lower)) notes.add("Mentions Tier 1 countries — check which ones count")

        // --- Platforms ---
        val yt = Regex("youtube|yt shorts|\\bshorts\\b").containsMatchIn(lower)
        val ig = Regex("instagram|\\breels?\\b|\\big\\b").containsMatchIn(lower)
        val tt = Regex("tiktok|tik tok").containsMatchIn(lower)
        val platform = when {
            yt && ig -> CampaignPlatform.BOTH
            yt -> CampaignPlatform.YOUTUBE
            ig -> CampaignPlatform.INSTAGRAM
            else -> null
        }
        if (tt) notes.add("Campaign also allows TikTok (this app checks YouTube/Instagram only)")

        val shortsOnly = if (Regex("shorts|reels|short-form|short form|tiktok").containsMatchIn(lower)) true else null

        return ParsedWhopRules(minViews, countryCode, countryPct, platform, shortsOnly, notes)
    }

    private fun toNumber(num: String, suffix: String): Long? {
        val clean = num.replace(",", "").trimEnd('.')
        val base = clean.toDoubleOrNull() ?: return null
        val mult = when (suffix) { "k" -> 1_000.0; "m" -> 1_000_000.0; else -> 1.0 }
        return (base * mult).toLong().takeIf { it > 0 }
    }
}
