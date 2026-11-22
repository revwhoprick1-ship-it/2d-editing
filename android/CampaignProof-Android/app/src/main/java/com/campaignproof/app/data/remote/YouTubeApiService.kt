package com.campaignproof.app.data.remote

import com.squareup.moshi.JsonClass
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface YouTubeDataApi {
    @GET("youtube/v3/channels")
    suspend fun getMyChannels(
        @Header("Authorization") authHeader: String,
        @Query("part") part: String = "snippet,statistics,contentDetails",
        @Query("mine") mine: Boolean = true,
        @Query("maxResults") maxResults: Int = 50
    ): ChannelsListResponse

    @GET("youtube/v3/playlistItems")
    suspend fun getPlaylistItems(
        @Header("Authorization") authHeader: String,
        @Query("part") part: String = "contentDetails",
        @Query("playlistId") playlistId: String,
        @Query("maxResults") maxResults: Int = 50
    ): PlaylistItemsResponse

    @GET("youtube/v3/videos")
    suspend fun getVideos(
        @Header("Authorization") authHeader: String,
        @Query("part") part: String = "snippet,statistics,contentDetails",
        @Query("id") idsCsv: String
    ): VideosListResponse
}

interface YouTubeAnalyticsApi {
    @GET("v2/reports")
    suspend fun queryReport(
        @Header("Authorization") authHeader: String,
        @Query("ids") ids: String = "channel==MINE",
        @Query("startDate") startDate: String,
        @Query("endDate") endDate: String,
        @Query("metrics") metrics: String,
        @Query("dimensions") dimensions: String,
        @Query("filters") filters: String,
        @Query("sort") sort: String? = null
    ): AnalyticsReportResponse
}

@JsonClass(generateAdapter = false)
data class ChannelsListResponse(val items: List<ChannelItem> = emptyList())

@JsonClass(generateAdapter = false)
data class ChannelItem(
    val id: String,
    val snippet: ChannelSnippet? = null,
    val statistics: ChannelStats? = null,
    val contentDetails: ChannelContentDetails? = null
)

@JsonClass(generateAdapter = false)
data class ChannelSnippet(
    val title: String? = null,
    val customUrl: String? = null,
    val thumbnails: ThumbnailMap? = null
)

@JsonClass(generateAdapter = false)
data class ChannelStats(val subscriberCount: String? = null)

@JsonClass(generateAdapter = false)
data class ChannelContentDetails(val relatedPlaylists: RelatedPlaylists? = null)

@JsonClass(generateAdapter = false)
data class RelatedPlaylists(val uploads: String? = null)

@JsonClass(generateAdapter = false)
data class ThumbnailMap(
    val default: ThumbnailUrl? = null,
    val medium: ThumbnailUrl? = null,
    val high: ThumbnailUrl? = null
)

@JsonClass(generateAdapter = false)
data class ThumbnailUrl(val url: String? = null)

@JsonClass(generateAdapter = false)
data class PlaylistItemsResponse(val items: List<PlaylistItem> = emptyList())

@JsonClass(generateAdapter = false)
data class PlaylistItem(val contentDetails: PlaylistItemContentDetails? = null)

@JsonClass(generateAdapter = false)
data class PlaylistItemContentDetails(val videoId: String? = null)

@JsonClass(generateAdapter = false)
data class VideosListResponse(val items: List<VideoItem> = emptyList())

@JsonClass(generateAdapter = false)
data class VideoItem(
    val id: String,
    val snippet: VideoSnippet? = null,
    val statistics: VideoStatistics? = null,
    val contentDetails: VideoContentDetails? = null
)

@JsonClass(generateAdapter = false)
data class VideoSnippet(
    val title: String? = null,
    val publishedAt: String? = null,
    val thumbnails: ThumbnailMap? = null
)

@JsonClass(generateAdapter = false)
data class VideoStatistics(val viewCount: String? = null)

@JsonClass(generateAdapter = false)
data class VideoContentDetails(val duration: String? = null)

@JsonClass(generateAdapter = false)
data class AnalyticsReportResponse(
    val rows: List<List<Any>>? = null
)

object ApiClientFactory {
    private val moshi: Moshi = Moshi.Builder()
        .add(KotlinJsonAdapterFactory())
        .build()

    private val okHttp: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .build()

    val youtubeDataApi: YouTubeDataApi = Retrofit.Builder()
        .baseUrl("https://www.googleapis.com/")
        .client(okHttp)
        .addConverterFactory(MoshiConverterFactory.create(moshi))
        .build()
        .create(YouTubeDataApi::class.java)

    val youtubeAnalyticsApi: YouTubeAnalyticsApi = Retrofit.Builder()
        .baseUrl("https://youtubeanalytics.googleapis.com/")
        .client(okHttp)
        .addConverterFactory(MoshiConverterFactory.create(moshi))
        .build()
        .create(YouTubeAnalyticsApi::class.java)

    val metaGraphApi: MetaGraphApi = Retrofit.Builder()
        .baseUrl("https://graph.facebook.com/v21.0/")
        .client(okHttp)
        .addConverterFactory(MoshiConverterFactory.create(moshi))
        .build()
        .create(MetaGraphApi::class.java)
}
