# CampaignProof — Native Android (Kotlin + Jetpack Compose) Build Guide

## Architecture Overview
- **UI**: Kotlin + Jetpack Compose + Material 3 Dark Theme (`ui/screens/*`)
- **Local Storage**: Room Database (`AccountEntity`, `CampaignEntity`, `ScannedVideoEntity`, `RecordingEntity`) + EncryptedSharedPreferences (Android Keystore) for OAuth tokens
- **YouTube Integration**: Google OAuth 2.0 PKCE via AppAuth (`YouTubeAuthManager.kt`), YouTube Data API v3 + YouTube Analytics API v2 (`YouTubeApiService.kt`)
- **Instagram Integration**: Meta Graph API (`MetaGraphApiService.kt`) + Manual Navigation Fallback when Meta Business API permissions or per-Reel country metrics are unavailable
- **Eligibility Engine**: `CampaignEligibilityEvaluator.kt` enforces strict 3-state evaluation (`ELIGIBLE` Green / `NOT_ELIGIBLE` Red / `INSUFFICIENT_DATA` Yellow) and never fabricates missing demographic data
- **Screen Recording**: `ScreenRecorderService.kt` Foreground Service (`foregroundServiceType="mediaProjection"`) using official `MediaProjection` + `MediaRecorder` saving H.264 MP4 files to `CampaignProof/<Platform>/<Account>/<Campaign>/<Video>.mp4`
- **Deterministic Navigation**: `StudioNavigationLauncher.kt` (Android Intents) + `CampaignProofAccessibilityService.kt` (view-node text/resource verification, zero blind coordinate clicking, mandatory safety stop & user confirmation gate before recording)

## Step 1: Obtain Google Cloud OAuth 2.0 Credentials (YouTube)
1. Open https://console.cloud.google.com/ and create or select a project.
2. Enable **YouTube Data API v3** and **YouTube Analytics API** under **APIs & Services -> Library**.
3. Configure the **OAuth consent screen** (External -> add your Google accounts as Test Users while in testing) with scopes:
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
4. Go to **Credentials -> Create Credentials -> OAuth client ID -> Android**:
   - Package name: `com.campaignproof.app`
   - SHA-1 signing certificate fingerprint: run `./gradlew signingReport` to get your debug/release SHA-1.
5. Copy the generated Client ID into `local.properties`:
   ```properties
   GOOGLE_OAUTH_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
   GOOGLE_OAUTH_REDIRECT_SCHEME=com.googleusercontent.apps.YOUR_CLIENT_ID_PREFIX
   ```

## Step 2: Obtain Meta Graph API Credentials (Optional — Instagram)
1. Open https://developers.facebook.com/ and create an app with **Instagram Graph API** / **Facebook Login for Business**.
2. Add your Instagram Business/Creator account linked to a Facebook Page.
3. Add `META_APP_ID` to `local.properties` (or use CampaignProof's built-in **Manual Navigation Fallback** if Meta API review is unavailable).

## Step 3: Build & Install the APK
1. Open this folder (`CampaignProof-Android`) in **Android Studio Ladybug (2024.2+)** with JDK 17.
2. Copy `local.properties.example` to `local.properties` and fill in your credentials.
3. Build a debug APK for a physical Android phone:
   ```bash
   ./gradlew assembleDebug
   ```
   Output APK: `app/build/outputs/apk/debug/app-debug.apk`
4. Build a signed release APK via **Build -> Generate Signed Bundle / APK** in Android Studio (`./gradlew assembleRelease`).
5. Install on a physical Android device (`Android 10 / API 29+`):
   ```bash
   adb install -r app/build/outputs/apk/debug/app-debug.apk
   ```
6. On first recording run:
   - Grant **Screen Recording (MediaProjection)** permission when Android prompts.
   - Optionally enable **CampaignProof Studio Navigation Assistant** in **Settings -> Accessibility** for deterministic YouTube Studio / Instagram navigation (never bypasses login or security prompts; stops for manual completion if any UI element is unexpected).
