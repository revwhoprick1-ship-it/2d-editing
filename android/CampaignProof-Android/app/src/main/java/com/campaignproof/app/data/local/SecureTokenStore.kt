package com.campaignproof.app.data.local

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

data class OAuthTokenBundle(
    val accessToken: String,
    val refreshToken: String?,
    val expiresAtEpochMs: Long
)

/**
 * Stores OAuth access and refresh tokens encrypted with Android Keystore AES256-GCM.
 * Passwords are never requested or stored.
 */
class SecureTokenStore(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "campaignproof_secure_tokens",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveTokens(accountId: String, bundle: OAuthTokenBundle) {
        prefs.edit()
            .putString("${accountId}_access", bundle.accessToken)
            .putString("${accountId}_refresh", bundle.refreshToken)
            .putLong("${accountId}_expires", bundle.expiresAtEpochMs)
            .apply()
    }

    fun getTokens(accountId: String): OAuthTokenBundle? {
        val access = prefs.getString("${accountId}_access", null) ?: return null
        val refresh = prefs.getString("${accountId}_refresh", null)
        val expires = prefs.getLong("${accountId}_expires", 0L)
        return OAuthTokenBundle(access, refresh, expires)
    }

    fun deleteTokens(accountId: String) {
        prefs.edit()
            .remove("${accountId}_access")
            .remove("${accountId}_refresh")
            .remove("${accountId}_expires")
            .apply()
    }
}
