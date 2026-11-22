package com.campaignproof.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val CanvasDark = Color(0xFF090D16)
val SurfaceDark = Color(0xFF111827)
val SurfaceElevated = Color(0xFF1E293B)
val BorderHairline = Color(0xFF1F2937)
val AccentCobalt = Color(0xFF2563EB)
val StatusGreen = Color(0xFF16A34A)
val StatusAmber = Color(0xFFD97706)
val StatusRed = Color(0xFFDC2626)

private val CampaignProofColorScheme = darkColorScheme(
    primary = AccentCobalt,
    onPrimary = Color.White,
    background = CanvasDark,
    onBackground = Color(0xFFF1F5F9),
    surface = SurfaceDark,
    onSurface = Color(0xFFF1F5F9),
    surfaceVariant = SurfaceElevated,
    onSurfaceVariant = Color(0xFF94A3B8),
    outline = BorderHairline,
    error = StatusRed,
    onError = Color.White
)

@Composable
fun CampaignProofTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CampaignProofColorScheme,
        content = content
    )
}
