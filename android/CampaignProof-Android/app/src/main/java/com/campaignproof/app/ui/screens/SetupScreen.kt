package com.campaignproof.app.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.campaignproof.app.BuildConfig
import com.campaignproof.app.data.local.AppSettingsState
import com.campaignproof.app.ui.theme.BorderHairline
import com.campaignproof.app.ui.theme.SurfaceDark

@Composable
fun SetupScreen(
    current: AppSettingsState,
    onSave: (AppSettingsState) -> Unit
) {
    var clientId by remember(current) { mutableStateOf(current.googleClientId) }
    var whopKey by remember(current) { mutableStateOf(current.whopApiKey) }
    var showKey by remember { mutableStateOf(false) }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        item {
            Text("Setup", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            Text(
                "Saved only on this phone, encrypted. Enter the same values on every device.",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF94A3B8)
            )
        }

        item {
            Card {
                Text("YouTube (Google OAuth)", fontWeight = FontWeight.SemiBold)
                OutlinedTextField(
                    value = clientId,
                    onValueChange = { clientId = it },
                    label = { Text("Google OAuth Client ID") },
                    placeholder = { Text("1234-abc.apps.googleusercontent.com") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Text(
                    "Google Cloud → Credentials → OAuth client ID → Android.\n" +
                        "Package name and redirect scheme (shown below) must match. " +
                        "In the client's Advanced settings, turn ON \"Custom URI scheme\".",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF94A3B8)
                )
                SelectionContainer {
                    Text(
                        "Package: ${BuildConfig.APPLICATION_ID}\n" +
                            "Redirect: ${BuildConfig.GOOGLE_OAUTH_REDIRECT_SCHEME}:/oauth2redirect",
                        fontFamily = FontFamily.Monospace,
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            }
        }

        item {
            Card {
                Text("Whop", fontWeight = FontWeight.SemiBold)
                OutlinedTextField(
                    value = whopKey,
                    onValueChange = { whopKey = it },
                    label = { Text("Whop API key") },
                    singleLine = true,
                    visualTransformation = if (showKey) VisualTransformation.None else PasswordVisualTransformation(),
                    modifier = Modifier.fillMaxWidth()
                )
                TextButton(onClick = { showKey = !showKey }) { Text(if (showKey) "Hide key" else "Show key") }
                Text(
                    "whop.com → Settings → Developer → API keys. Used to read Content Rewards " +
                        "campaigns from a submission ID (Rules tab → Import from Whop).",
                    style = MaterialTheme.typography.bodySmall,
                    color = Color(0xFF94A3B8)
                )
            }
        }

        item {
            Button(
                onClick = { onSave(AppSettingsState(googleClientId = clientId, whopApiKey = whopKey)) },
                modifier = Modifier.fillMaxWidth()
            ) { Text("Save Setup") }
        }

        item {
            Text(
                "Instagram uses the manual fallback (add @handle in Accounts) — no key needed.",
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFF94A3B8)
            )
        }
    }
}

@Composable
private fun Card(content: @Composable () -> Unit) {
    Surface(color = SurfaceDark, border = BorderStroke(1.dp, BorderHairline), shape = MaterialTheme.shapes.medium) {
        Column(modifier = Modifier.padding(14.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            content()
        }
    }
}
