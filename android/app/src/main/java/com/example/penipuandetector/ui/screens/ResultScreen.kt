package com.example.penipuandetector.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.penipuandetector.ui.components.ProbabilityBar
import com.example.penipuandetector.ui.components.ScreenHeader
import com.example.penipuandetector.ui.components.SectionLabel
import com.example.penipuandetector.ui.formatTimestamp
import com.example.penipuandetector.ui.theme.Danger
import com.example.penipuandetector.ui.theme.DangerSoft
import com.example.penipuandetector.ui.theme.Ink
import com.example.penipuandetector.ui.theme.Line
import com.example.penipuandetector.ui.theme.Muted
import com.example.penipuandetector.ui.theme.Safe
import com.example.penipuandetector.ui.theme.SafeSoft
import com.example.penipuandetector.ui.theme.Teal
import com.example.penipuandetector.ui.viewmodel.ResultViewModel

@Composable
fun ResultScreen(
    onBack: () -> Unit,
    onDetectAgain: () -> Unit,
    onHistory: () -> Unit,
    viewModel: ResultViewModel = viewModel(factory = ResultViewModel.Factory),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(topBar = { ScreenHeader(title = "Hasil Deteksi", onBack = onBack) }) { innerPadding ->
        when {
            state.isLoading -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(color = Teal)
            }

            state.detection == null -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(24.dp),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = "Hasil deteksi tidak ditemukan.",
                    style = MaterialTheme.typography.bodyLarge,
                    color = Muted,
                    textAlign = TextAlign.Center,
                )
            }

            else -> {
                val detection = state.detection!!
                val isFraud = detection.isFraud
                val accent = if (isFraud) Danger else Safe
                val soft = if (isFraud) DangerSoft else SafeSoft

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(innerPadding)
                        .verticalScroll(rememberScrollState())
                        .padding(horizontal = 20.dp, vertical = 12.dp),
                ) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = soft,
                        shape = MaterialTheme.shapes.extraLarge,
                        border = BorderStroke(1.dp, accent.copy(alpha = 0.18f)),
                    ) {
                        Column(
                            modifier = Modifier.padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Surface(color = Color.White, shape = CircleShape, modifier = Modifier.size(68.dp)) {
                                Box(contentAlignment = Alignment.Center) {
                                    Icon(
                                        imageVector = if (isFraud) {
                                            Icons.Rounded.Warning
                                        } else {
                                            Icons.Rounded.CheckCircle
                                        },
                                        contentDescription = null,
                                        tint = accent,
                                        modifier = Modifier.size(36.dp),
                                    )
                                }
                            }
                            Spacer(Modifier.height(16.dp))
                            Text(
                                text = detection.label,
                                style = MaterialTheme.typography.headlineMedium,
                                color = accent,
                                textAlign = TextAlign.Center,
                            )
                            Spacer(Modifier.height(8.dp))
                            Text(
                                text = if (isFraud) {
                                    "Pesan ini terindikasi sebagai penipuan. Jangan membalas, jangan klik tautan, dan jangan kirim data pribadi."
                                } else {
                                    "Model tidak menemukan indikasi penipuan yang kuat pada pesan ini."
                                },
                                style = MaterialTheme.typography.bodyMedium,
                                color = Ink.copy(alpha = 0.75f),
                                textAlign = TextAlign.Center,
                            )
                        }
                    }

                    Spacer(Modifier.height(20.dp))
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.colorScheme.surface,
                        shape = MaterialTheme.shapes.large,
                        border = BorderStroke(1.dp, Line),
                    ) {
                        Column(modifier = Modifier.padding(18.dp)) {
                            SectionLabel("Probabilitas Kelas")
                            Spacer(Modifier.height(16.dp))
                            ProbabilityBar(
                                label = "Penipuan",
                                probability = detection.probabilityFraud,
                                color = Danger,
                            )
                            Spacer(Modifier.height(16.dp))
                            ProbabilityBar(
                                label = "Bukan Penipuan",
                                probability = detection.probabilityHam,
                                color = Safe,
                            )
                        }
                    }

                    Spacer(Modifier.height(20.dp))
                    SectionLabel("Pesan Asli")
                    Spacer(Modifier.height(8.dp))
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = MaterialTheme.colorScheme.surface,
                        shape = MaterialTheme.shapes.large,
                        border = BorderStroke(1.dp, Line),
                    ) {
                        Text(
                            text = detection.message,
                            modifier = Modifier.padding(16.dp),
                            style = MaterialTheme.typography.bodyLarge,
                            color = Ink,
                        )
                    }

                    if (detection.processedText.isNotBlank()) {
                        Spacer(Modifier.height(16.dp))
                        SectionLabel("Teks Setelah Preprocessing")
                        Spacer(Modifier.height(8.dp))
                        Surface(
                            modifier = Modifier.fillMaxWidth(),
                            color = MaterialTheme.colorScheme.surfaceVariant,
                            shape = MaterialTheme.shapes.medium,
                        ) {
                            Text(
                                text = detection.processedText,
                                modifier = Modifier.padding(14.dp),
                                style = MaterialTheme.typography.bodyMedium,
                                color = Muted,
                            )
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    Text(
                        text = "Dideteksi pada ${formatTimestamp(detection.createdAt)}",
                        style = MaterialTheme.typography.labelMedium,
                        color = Muted,
                    )

                    Spacer(Modifier.height(24.dp))
                    Button(
                        onClick = onDetectAgain,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = MaterialTheme.shapes.medium,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = Teal,
                            contentColor = Color.White,
                        ),
                    ) {
                        Icon(Icons.Rounded.Search, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.size(8.dp))
                        Text("Deteksi Pesan Lain", fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.height(10.dp))
                    OutlinedButton(
                        onClick = onHistory,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp),
                        shape = MaterialTheme.shapes.medium,
                        border = BorderStroke(1.dp, Line),
                    ) {
                        Icon(Icons.Rounded.History, contentDescription = null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.size(8.dp))
                        Text("Lihat Riwayat", color = Ink)
                    }
                    Spacer(Modifier.height(8.dp))
                }
            }
        }
    }
}
