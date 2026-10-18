package com.example.penipuandetector.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.text.KeyboardOptions
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.penipuandetector.ui.components.ErrorCard
import com.example.penipuandetector.ui.components.ScreenHeader
import com.example.penipuandetector.ui.theme.Ink
import com.example.penipuandetector.ui.theme.Line
import com.example.penipuandetector.ui.theme.Muted
import com.example.penipuandetector.ui.theme.SurfaceWhite
import com.example.penipuandetector.ui.theme.Teal
import com.example.penipuandetector.ui.theme.TealLight
import com.example.penipuandetector.ui.viewmodel.DetectViewModel
import com.example.penipuandetector.ui.viewmodel.MAX_MESSAGE_LENGTH

private const val SAMPLE_FRAUD =
    "Congratulations! You have won a 1000 cash prize. Call 08001234567 now to claim your reward."
private const val SAMPLE_HAM = "Hi, are we still meeting for lunch tomorrow at noon?"

@Composable
fun DetectScreen(
    onBack: () -> Unit,
    onResult: (Long) -> Unit,
    viewModel: DetectViewModel = viewModel(factory = DetectViewModel.Factory),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(state.savedDetectionId) {
        state.savedDetectionId?.let { id ->
            viewModel.consumeNavigation()
            onResult(id)
        }
    }

    Scaffold(topBar = { ScreenHeader(title = "Deteksi Pesan", onBack = onBack) }) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .imePadding()
                .padding(horizontal = 20.dp, vertical = 12.dp),
        ) {
            Text(
                text = "Tempel pesan yang ingin diperiksa",
                style = MaterialTheme.typography.titleLarge,
                color = Ink,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Salin pesan SMS atau WhatsApp yang Anda terima, lalu tekan Lakukan Deteksi.",
                style = MaterialTheme.typography.bodyMedium,
                color = Muted,
            )

            Spacer(Modifier.height(18.dp))
            OutlinedTextField(
                value = state.message,
                onValueChange = viewModel::onMessageChange,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(min = 190.dp),
                enabled = !state.isLoading,
                placeholder = {
                    Text(
                        "Contoh: Selamat! Anda memenangkan hadiah. Hubungi nomor berikut...",
                        color = Muted.copy(alpha = 0.8f),
                    )
                },
                supportingText = {
                    Text("${state.message.length} / $MAX_MESSAGE_LENGTH karakter")
                },
                keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences),
                shape = MaterialTheme.shapes.large,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Teal,
                    unfocusedBorderColor = Line,
                    focusedContainerColor = SurfaceWhite,
                    unfocusedContainerColor = SurfaceWhite,
                ),
            )

            Spacer(Modifier.height(12.dp))
            Text(
                text = "Coba contoh pesan",
                style = MaterialTheme.typography.labelMedium,
                color = Muted,
                fontWeight = FontWeight.SemiBold,
            )
            Spacer(Modifier.height(6.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(
                    onClick = { viewModel.onMessageChange(SAMPLE_FRAUD) },
                    enabled = !state.isLoading,
                    label = { Text("Penipuan") },
                    leadingIcon = {
                        Icon(
                            Icons.Rounded.Search,
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                        )
                    },
                )
                AssistChip(
                    onClick = { viewModel.onMessageChange(SAMPLE_HAM) },
                    enabled = !state.isLoading,
                    label = { Text("Pesan normal") },
                )
            }

            Spacer(Modifier.height(22.dp))
            Button(
                onClick = viewModel::detect,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(54.dp),
                enabled = !state.isLoading,
                shape = MaterialTheme.shapes.medium,
                colors = ButtonDefaults.buttonColors(containerColor = Teal, contentColor = Color.White),
            ) {
                if (state.isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = Color.White,
                    )
                    Spacer(Modifier.size(10.dp))
                    Text("Mendeteksi...", fontWeight = FontWeight.Bold)
                } else {
                    Text("Lakukan Deteksi", fontWeight = FontWeight.Bold)
                }
            }

            if (state.error != null) {
                Spacer(Modifier.height(16.dp))
                ErrorCard(message = state.error!!, onRetry = viewModel::detect)
            }

            Spacer(Modifier.height(24.dp))
            Surface(
                color = TealLight,
                shape = MaterialTheme.shapes.medium,
                border = BorderStroke(1.dp, Teal.copy(alpha = 0.12f)),
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Surface(color = Color.White, shape = CircleShape, modifier = Modifier.size(32.dp)) {
                        androidx.compose.foundation.layout.Box(contentAlignment = Alignment.Center) {
                            Icon(
                                Icons.Rounded.Info,
                                contentDescription = null,
                                tint = Teal,
                                modifier = Modifier.size(17.dp),
                            )
                        }
                    }
                    Spacer(Modifier.size(10.dp))
                    Text(
                        text = "Model dilatih pada dataset SMS berbahasa Inggris. Gunakan pesan berbahasa Inggris untuk hasil terbaik.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Ink.copy(alpha = 0.78f),
                    )
                }
            }
        }
    }
}
