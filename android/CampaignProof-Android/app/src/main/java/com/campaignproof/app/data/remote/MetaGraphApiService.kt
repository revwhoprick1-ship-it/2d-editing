package com.campaignproof.app.data.remote

import com.squareup.moshi.JsonClass
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

/**
 * Official Meta Graph API interface for Instagram Professional (Business / Creator) accounts.
 * Note: Meta Graph API does not provide per-Reel country demographic percentages on standard tiers;
 * CampaignProof explicitly surfaces this as INSUFFICIENT_DATA (Yellow) with manual confirmation fallback.
 */
interface MetaGraphApi {
    @GET("me/accounts")
    suspend fun getLinkedPages(
        @Query("fields") fields: String = "id,name,instagram_business_account{id,username,name,profile_picture_url,followers_count}",
        @Query("access_token") accessToken: String
    ): MetaPagesResponse

    @GET("{igUserId}/media")
    suspend fun getMediaList(
        @Path("igUserId") igUserId: String,
        @Query("fields") fields: String = "id,caption,media_type,media_product_type,permalink,thumbnail_url,timestamp",
        @Query("limit") limit: Int = 35,
        @Query("access_token") accessToken: String
    ): MetaMediaListResponse

    @GET("{mediaId}/insights")
    suspend fun getMediaInsights(
        @Path("mediaId") mediaId: String,
        @Query("metric") metric: String = "views,reach",
        @Query("access_token") accessToken: String
    ): MetaInsightsResponse
}

@JsonClass(generateAdapter = false)
data class MetaPagesResponse(val data: List<MetaPageItem> = emptyList())

@JsonClass(generateAdapter = false)
data class MetaPageItem(
    val id: String,
    val name: String? = null,
    val instagram_business_account: InstagramBusinessAccount? = null
)

@JsonClass(generateAdapter = false)
data class InstagramBusinessAccount(
    val id: String,
    val username: String? = null,
    val name: String? = null,
    val profile_picture_url: String? = null,
    val followers_count: Long? = null
)

@JsonClass(generateAdapter = false)
data class MetaMediaListResponse(val data: List<MetaMediaItem> = emptyList())

@JsonClass(generateAdapter = false)
data class MetaMediaItem(
    val id: String,
    val caption: String? = null,
    val media_type: String? = null,
    val media_product_type: String? = null,
    val permalink: String? = null,
    val thumbnail_url: String? = null,
    val timestamp: String? = null
)

@JsonClass(generateAdapter = false)
data class MetaInsightsResponse(val data: List<MetaInsightMetric> = emptyList())

@JsonClass(generateAdapter = false)
data class MetaInsightMetric(
    val name: String,
    val values: List<MetaInsightValue> = emptyList()
)

@JsonClass(generateAdapter = false)
data class MetaInsightValue(val value: Long? = null)
