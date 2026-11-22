import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
}

val localProps = Properties().apply {
    val file = rootProject.file("local.properties")
    if (file.exists()) {
        file.inputStream().use { load(it) }
    }
}

fun prop(key: String, default: String = ""): String =
    (localProps.getProperty(key) ?: System.getenv(key) ?: default).trim()

android {
    namespace = "com.campaignproof.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.campaignproof.app"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // Read OAuth client IDs from local.properties (never hardcode credentials)
        val googleAndroidClientId = prop("GOOGLE_OAUTH_CLIENT_ID")
        val googleRedirectScheme = prop("GOOGLE_OAUTH_REDIRECT_SCHEME", "com.campaignproof.app")
        val metaAppId = prop("META_APP_ID")
        val metaRedirectUri = prop("META_OAUTH_REDIRECT_URI", "com.campaignproof.app://meta-oauth")

        buildConfigField("String", "GOOGLE_OAUTH_CLIENT_ID", "\"$googleAndroidClientId\"")
        buildConfigField("String", "GOOGLE_OAUTH_REDIRECT_SCHEME", "\"$googleRedirectScheme\"")
        buildConfigField("String", "META_APP_ID", "\"$metaAppId\"")
        buildConfigField("String", "META_OAUTH_REDIRECT_URI", "\"$metaRedirectUri\"")

        manifestPlaceholders["appAuthRedirectScheme"] = googleRedirectScheme
    }

    // One fixed signing key for every build, so the same APK installs/updates on all phones
    // and the SHA-1 registered in Google Cloud never changes. Provided by CI secrets.
    val signingFile = prop("CP_KEYSTORE_FILE")
    val sharedSigning = if (signingFile.isNotBlank() && file(signingFile).exists()) {
        signingConfigs.create("shared") {
            storeFile = file(signingFile)
            storePassword = prop("CP_KEYSTORE_PASSWORD")
            keyAlias = prop("CP_KEY_ALIAS", "campaignproof")
            keyPassword = prop("CP_KEYSTORE_PASSWORD")
        }
    } else null

    buildTypes {
        debug {
            if (sharedSigning != null) signingConfig = sharedSigning
        }
        release {
            if (sharedSigning != null) signingConfig = sharedSigning
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.navigation.compose)

    // Room local persistence
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    // Encrypted OAuth token storage backed by Android Keystore
    implementation(libs.androidx.security.crypto)

    // Networking & JSON
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.moshi)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.moshi.kotlin)
    implementation(libs.kotlinx.coroutines.android)

    // Google OAuth 2.0 PKCE (AppAuth)
    implementation(libs.openid.appauth)

    // Thumbnails
    implementation(libs.coil.compose)

    debugImplementation(libs.androidx.ui.tooling)
}
