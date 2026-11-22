package com.campaignproof.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

enum class Platform { YOUTUBE, INSTAGRAM }
enum class CampaignPlatform { YOUTUBE, INSTAGRAM, BOTH }
enum class AuthMode { GOOGLE_OAUTH, META_GRAPH_API, MANUAL_FALLBACK }
enum class TokenStatus { ACTIVE, TOKEN_EXPIRED, MANUAL_ONLY, ERROR }
enum class EligibilityStatus { ELIGIBLE, NOT_ELIGIBLE, INSUFFICIENT_DATA }
enum class RecordingStatus { COMPLETED, VERIFIED, NEEDS_RETAKE }

@Entity(tableName = "accounts")
data class AccountEntity(
    @PrimaryKey val id: String,
    val platform: Platform,
    val externalId: String,
    val name: String,
    val handle: String,
    val avatarUrl: String?,
    val subscriberCount: Long?,
    val uploadsPlaylistId: String?,
    val authMode: AuthMode,
    val tokenStatus: TokenStatus,
    val selectedForScan: Boolean = true,
    val lastError: String? = null,
    val connectedAtEpochMs: Long,
    val lastScannedAtEpochMs: Long? = null
)

@Entity(tableName = "campaigns")
data class CampaignEntity(
    @PrimaryKey val id: String,
    val name: String,
    val platform: CampaignPlatform,
    val minViews: Long,
    val targetCountryCode: String,
    val targetCountryName: String,
    val minCountryPercentage: Double,
    val requiredAgeGroupsCsv: String, // e.g. "18-24,25-34"
    val minAgeGroupPercentage: Double?,
    val requiredGender: String, // "ANY" | "MALE" | "FEMALE"
    val minGenderPercentage: Double?,
    val shortsOrReelsOnly: Boolean,
    val publishedAfterIso: String?,
    val requiredKeyword: String?,
    val isActive: Boolean,
    val updatedAtEpochMs: Long
)

@Entity(tableName = "scanned_videos")
data class ScannedVideoEntity(
    @PrimaryKey val id: String,
    val externalVideoId: String,
    val accountId: String,
    val accountName: String,
    val accountHandle: String,
    val platform: Platform,
    val title: String,
    val videoUrl: String,
    val studioAnalyticsUrl: String,
    val thumbnailUrl: String?,
    val publishedAtIso: String,
    val durationSeconds: Int?,
    val isShortOrReel: Boolean,
    val viewCount: Long?,
    val targetCountryCode: String,
    val targetCountryPercentage: Double?, // Strictly null when API does not provide data
    val countryBreakdownJson: String,
    val demographicsJson: String,
    val demographicsAvailable: Boolean,
    val dataAvailabilityNotesJson: String,
    val campaignId: String,
    val eligibilityStatus: EligibilityStatus,
    val ruleSummary: String,
    val scannedAtEpochMs: Long
)

@Entity(tableName = "recordings")
data class RecordingEntity(
    @PrimaryKey val id: String,
    val videoId: String,
    val externalVideoId: String,
    val videoTitle: String,
    val videoUrl: String,
    val platform: Platform,
    val accountId: String,
    val accountName: String,
    val campaignId: String,
    val campaignName: String,
    val relativePath: String, // CampaignProof/<Platform>/<Account>/<Campaign>/<Video>.mp4
    val absoluteFilePath: String,
    val fileSizeBytes: Long,
    val durationSeconds: Int,
    val viewCountAtScan: Long?,
    val targetCountryCode: String,
    val targetCountryPercentage: Double?,
    val demographicsSummary: String,
    val campaignRequirementsSnapshotJson: String,
    val recordedAtEpochMs: Long,
    val status: RecordingStatus = RecordingStatus.COMPLETED
)
