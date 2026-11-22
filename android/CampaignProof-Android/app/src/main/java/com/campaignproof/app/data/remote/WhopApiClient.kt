package com.campaignproof.app.data.remote

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

/** What we could read from Whop for one campaign (Whop API calls these "bounties"). */
data class WhopCampaignInfo(
    val bountyId: String,
    val submissionId: String?,
    val title: String,
    val description: String,
    val status: String?,
    /** All other simple fields Whop returned, shown to the user as-is (never guessed). */
    val extraFields: List<Pair<String, String>>,
    val submissionLinks: List<String>
)

class WhopApiException(message: String) : Exception(message)

/**
 * Reads Content Rewards campaigns from Whop's public REST API (https://api.whop.com/api/v1).
 *
 * Input can be a submission ID (btys_...), a campaign/bounty ID, or a whop.com URL containing one.
 * Response JSON is parsed loosely because Whop's bounty API is still in beta: every field that is
 * present is surfaced, missing fields are left empty.
 */
class WhopApiClient(private val apiKeyProvider: () -> String) {
    private val http = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .build()

    suspend fun lookup(rawInput: String): WhopCampaignInfo = withContext(Dispatchers.IO) {
        val input = rawInput.trim()
        if (input.isEmpty()) throw WhopApiException("Paste a Whop submission ID or campaign ID.")

        val submissionId = SUBMISSION_ID.find(input)?.value
        if (submissionId != null) {
            val sub = getJson("bounty_submissions/$submissionId")
            val bountyId = sub.optString("bounty_id").ifBlank {
                sub.optJSONObject("bounty")?.optString("id").orEmpty()
            }
            if (bountyId.isBlank()) {
                throw WhopApiException("Whop returned the submission but no campaign (bounty_id) in it.")
            }
            val bounty = getJson("bounties/$bountyId")
            return@withContext toInfo(bounty, bountyId, submissionId, collectLinks(sub))
        }

        val bountyId = ANY_ID.findAll(input).map { it.value }.firstOrNull()
            ?: input.substringAfterLast('/').substringBefore('?').ifBlank { input }
        val bounty = getJson("bounties/$bountyId")
        toInfo(bounty, bountyId, null, emptyList())
    }

    private fun getJson(path: String): JSONObject {
        val key = apiKeyProvider()
        val builder = Request.Builder()
            .url("$BASE_URL$path")
            .header("Accept", "application/json")
        if (key.isNotBlank()) builder.header("Authorization", "Bearer $key")

        http.newCall(builder.build()).execute().use { resp ->
            val body = resp.body?.string().orEmpty()
            if (!resp.isSuccessful) {
                val msg = runCatching {
                    val o = JSONObject(body)
                    o.optJSONObject("error")?.optString("message")?.ifBlank { null } ?: o.optString("message")
                }.getOrNull().orEmpty()
                val hint = when (resp.code) {
                    401, 403 -> " Check the Whop API key in Setup (it needs read access to bounties)."
                    404 -> " ID not found — check it was copied fully."
                    else -> ""
                }
                throw WhopApiException("Whop API ${resp.code} on /$path. $msg$hint".trim())
            }
            return runCatching { JSONObject(body) }.getOrElse {
                throw WhopApiException("Whop returned something that is not JSON for /$path")
            }
        }
    }

    private fun toInfo(o: JSONObject, bountyId: String, submissionId: String?, links: List<String>): WhopCampaignInfo {
        val skip = setOf("id", "title", "name", "description", "status")
        val extras = mutableListOf<Pair<String, String>>()
        flatten("", o, extras)
        return WhopCampaignInfo(
            bountyId = o.optString("id").ifBlank { bountyId },
            submissionId = submissionId,
            title = o.optString("title").ifBlank { o.optString("name") }.ifBlank { "Whop campaign $bountyId" },
            description = o.optString("description"),
            status = o.optString("status").ifBlank { null },
            extraFields = extras.filter { it.first !in skip },
            submissionLinks = links
        )
    }

    private fun flatten(prefix: String, o: JSONObject, out: MutableList<Pair<String, String>>) {
        for (k in o.keys()) {
            val v = o.opt(k)
            val name = if (prefix.isEmpty()) k else "$prefix.$k"
            when (v) {
                null, JSONObject.NULL -> Unit
                is JSONObject -> if (prefix.count { it == '.' } < 1) flatten(name, v, out)
                is JSONArray -> {
                    val simple = (0 until v.length()).map { v.opt(it) }
                        .filter { it !is JSONObject && it !is JSONArray && it != JSONObject.NULL }
                    if (simple.isNotEmpty()) out.add(name to simple.joinToString(", "))
                }
                else -> v.toString().takeIf { it.isNotBlank() }?.let { out.add(name to it) }
            }
        }
    }

    private fun collectLinks(o: JSONObject): List<String> =
        URL_REGEX.findAll(o.toString().replace("\\/", "/")).map { it.value }.distinct().toList()

    companion object {
        const val BASE_URL = "https://api.whop.com/api/v1/"
        private val SUBMISSION_ID = Regex("btys_[A-Za-z0-9]+")
        private val ANY_ID = Regex("\\b[a-z]{2,6}_[A-Za-z0-9]{6,}\\b")
        private val URL_REGEX = Regex("https?://[^\"\\s,]+")
    }
}
