package com.campaignproof.app.data.local

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.campaignproof.app.BuildConfig
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AppSettingsState(
    val googleClientId: String = "",
    val whopApiKey: String = ""
)

/**
 * Per-device credentials entered inside the app (Setup tab), so one APK works on many phones.
 * Stored encrypted with the Android Keystore. Build-time values from local.properties are
 * only used as a fallback when nothing was entered on the device.
 */
class AppSettings(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs = EncryptedSharedPreferences.create(
        context,
        "campaignproof_settings",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    private val _state = MutableStateFlow(read())
    val state: StateFlow<AppSettingsState> = _state.asStateFlow()

    private fun read() = AppSettingsState(
        googleClientId = prefs.getString(KEY_GOOGLE_CLIENT_ID, null).orEmpty(),
        whopApiKey = prefs.getString(KEY_WHOP_API_KEY, null).orEmpty()
    )

    /** Client ID entered on this device, else the one baked into the build (may be empty). */
    val googleClientId: String
        get() = _state.value.googleClientId.ifBlank { BuildConfig.GOOGLE_OAUTH_CLIENT_ID }.trim()

    val whopApiKey: String
        get() = _state.value.whopApiKey.trim()

    fun save(newState: AppSettingsState) {
        prefs.edit()
            .putString(KEY_GOOGLE_CLIENT_ID, newState.googleClientId.trim())
            .putString(KEY_WHOP_API_KEY, newState.whopApiKey.trim())
            .apply()
        _state.value = read()
    }

    companion object {
        private const val KEY_GOOGLE_CLIENT_ID = "google_client_id"
        private const val KEY_WHOP_API_KEY = "whop_api_key"
    }
}
