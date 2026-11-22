package com.campaignproof.app.data.remote

import android.content.Context
import android.content.Intent
import android.net.Uri
import com.campaignproof.app.BuildConfig
import com.campaignproof.app.data.local.OAuthTokenBundle
import kotlinx.coroutines.suspendCancellableCoroutine
import net.openid.appauth.AuthorizationException
import net.openid.appauth.AuthorizationRequest
import net.openid.appauth.AuthorizationResponse
import net.openid.appauth.AuthorizationService
import net.openid.appauth.AuthorizationServiceConfiguration
import net.openid.appauth.GrantTypeValues
import net.openid.appauth.ResponseTypeValues
import net.openid.appauth.TokenRequest
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * Implements Google OAuth 2.0 PKCE via AppAuth for connecting multiple YouTube channels
 * without ever collecting Google account passwords inside CampaignProof.
 */
class YouTubeAuthManager(context: Context, private val clientIdProvider: () -> String) {
    private val authService = AuthorizationService(context.applicationContext)

    private val serviceConfig = AuthorizationServiceConfiguration(
        Uri.parse("https://accounts.google.com/o/oauth2/v2/auth"),
        Uri.parse("https://oauth2.googleapis.com/token")
    )

    private val clientId: String get() = clientIdProvider().trim()

    fun isConfigured(): Boolean = clientId.isNotBlank()

    fun createAuthorizationIntent(): Intent {
        require(isConfigured()) {
            "Google OAuth Client ID is empty. Enter it in the Setup tab."
        }
        val redirectUri = Uri.parse("${BuildConfig.GOOGLE_OAUTH_REDIRECT_SCHEME}:/oauth2redirect")
        val request = AuthorizationRequest.Builder(
            serviceConfig,
            clientId,
            ResponseTypeValues.CODE,
            redirectUri
        )
            .setScopes(
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/yt-analytics.readonly"
            )
            .setPromptValues("consent", "select_account")
            .setAdditionalParameters(mapOf("access_type" to "offline"))
            .build()

        return authService.getAuthorizationRequestIntent(request)
    }

    suspend fun handleAuthResult(intent: Intent): OAuthTokenBundle {
        val response = AuthorizationResponse.fromIntent(intent)
        val exception = AuthorizationException.fromIntent(intent)
        if (exception != null) {
            throw IllegalStateException("Google OAuth failed: ${exception.errorDescription ?: exception.message}")
        }
        if (response == null) {
            throw IllegalStateException("No OAuth response received.")
        }

        return suspendCancellableCoroutine { cont ->
            authService.performTokenRequest(response.createTokenExchangeRequest()) { tokenResp, tokenEx ->
                if (tokenEx != null || tokenResp?.accessToken == null) {
                    cont.resumeWithException(
                        IllegalStateException(
                            tokenEx?.errorDescription ?: "Token exchange failed"
                        )
                    )
                } else {
                    cont.resume(
                        OAuthTokenBundle(
                            accessToken = tokenResp.accessToken!!,
                            refreshToken = tokenResp.refreshToken,
                            expiresAtEpochMs = tokenResp.accessTokenExpirationTime
                                ?: (System.currentTimeMillis() + 3600_000L)
                        )
                    )
                }
            }
        }
    }

    suspend fun refreshAccessToken(refreshToken: String): OAuthTokenBundle {
        val request = TokenRequest.Builder(serviceConfig, clientId)
            .setGrantType(GrantTypeValues.REFRESH_TOKEN)
            .setRefreshToken(refreshToken)
            .build()

        return suspendCancellableCoroutine { cont ->
            authService.performTokenRequest(request) { tokenResp, tokenEx ->
                if (tokenEx != null || tokenResp?.accessToken == null) {
                    cont.resumeWithException(
                        IllegalStateException(
                            tokenEx?.errorDescription ?: "Failed to refresh expired YouTube token"
                        )
                    )
                } else {
                    cont.resume(
                        OAuthTokenBundle(
                            accessToken = tokenResp.accessToken!!,
                            refreshToken = tokenResp.refreshToken ?: refreshToken,
                            expiresAtEpochMs = tokenResp.accessTokenExpirationTime
                                ?: (System.currentTimeMillis() + 3600_000L)
                        )
                    )
                }
            }
        }
    }

    fun dispose() {
        authService.dispose()
    }
}
