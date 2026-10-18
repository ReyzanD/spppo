package com.example.penipuandetector.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
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
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.penipuandetector.BuildConfig
import com.example.penipuandetector.data.remote.ModelInfoResponse
import com.example.penipuandetector.ui.asPercent
import com.example.penipuandetector.ui.components.DividerLine
import com.example.penipuandetector.ui.components.ErrorCard
import com.example.penipuandetector.ui.components.InfoRow
import com.example.penipuandetector.ui.components.ScreenHeader
import com.example.penipuandetector.ui.components.SectionLabel
import com.example.penipuandetector.ui.formatIsoDate
import com.example.penipuandetector.ui.formatNumber
import com.example.penipuandetector.ui.theme.Amber
import com.example.penipuandetector.ui.theme.Ink
import com.example.penipuandetector.ui.theme.InkSoft
import com.example.penipuandetector.ui.theme.Line
import com.example.penipuandetector.ui.theme.Muted
import com.example.penipuandetector.ui.theme.Teal
import com.example.penipuandetector.ui.theme.TealLight
import com.example.penipuandetector.ui.viewmodel.ModelInfoViewModel

@Composable
fun ModelInfoScreen(
    onBack: () -> Unit,
    viewModel: ModelInfoViewModel = viewModel(factory = ModelInfoViewModel.Factory),
) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(topBar = { ScreenHeader(title = "Informasi Model", onBack = onBack) }) { innerPadding ->
        when {
            state.isLoading -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentAlignment = Alignment.Center,
            ) {
                CircularProgressIndicator(color = Teal)
            }

            state.error != null -> Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .padding(20.dp),
                contentAlignment = Alignment.Center,
            ) {
                ErrorCard(message = state.error!!, onRetry = viewModel::load)
            }

            state.info != null -> ModelInfoContent(
                info = state.info!!,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
            )
        }
    }
}

@Composable
private fun ModelInfoContent(info: ModelInfoResponse, modifier: Modifier = Modifier) {
    val datasetSize = info.dataset?.size ?: info.datasetSize
    val testRatio = info.split?.testSize ?: 0.2

    Column(
        modifier = modifier
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp, vertical = 12.dp),
    ) {
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = Color.Transparent,
            shape = MaterialTheme.shapes.extraLarge,
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(
                        brush = Brush.linearGradient(listOf(Ink, InkSoft)),
                        shape = MaterialTheme.shapes.extraLarge,
                    )
                    .padding(22.dp),
            ) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(
                            color = Amber,
                            shape = CircleShape,
                            modifier = Modifier.size(30.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    Icons.Rounded.Info,
                                    contentDescription = null,
                                    tint = Ink,
                                    modifier = Modifier.size(17.dp),
                                )
                            }
                        }
                        Spacer(Modifier.size(10.dp))
                        Text(
                            text = "AKURASI PADA DATA UJI",
                            style = MaterialTheme.typography.labelMedium,
                            color = Amber,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                    Spacer(Modifier.height(14.dp))
                    Text(
                        text = (info.accuracy / 100.0).asPercent(2),
                        style = MaterialTheme.typography.displaySmall,
                        color = Color.White,
                    )
                    Spacer(Modifier.height(4.dp))
                    Text(
                        text = info.algorithm,
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White.copy(alpha = 0.86f),
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        text = "Diukur pada ${formatNumber(info.testSize)} pesan uji yang tidak dipakai saat pelatihan.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Color.White.copy(alpha = 0.6f),
                    )
                }
            }
        }

        Spacer(Modifier.height(18.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            MetricTile(
                label = "Presisi",
                value = info.metrics?.precision?.let { (it / 100.0).asPercent(2) } ?: "-",
                modifier = Modifier.weight(1f),
            )
            MetricTile(
                label = "Recall",
                value = info.metrics?.recall?.let { (it / 100.0).asPercent(2) } ?: "-",
                modifier = Modifier.weight(1f),
            )
            MetricTile(
                label = "F1-score",
                value = info.metrics?.f1?.let { (it / 100.0).asPercent(2) } ?: "-",
                modifier = Modifier.weight(1f),
            )
        }

        Spacer(Modifier.height(24.dp))
        SectionLabel("Detail Model")
        Spacer(Modifier.height(8.dp))
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = MaterialTheme.colorScheme.surface,
            shape = MaterialTheme.shapes.large,
            border = BorderStroke(1.dp, Line),
        ) {
            Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
                InfoRow("Algoritma", info.algorithm)
                DividerLine()
                InfoRow("Vektor fitur", info.vectorizer)
                DividerLine()
                InfoRow("Dataset", info.dataset?.name ?: "UCI SMS Spam Collection")
                DividerLine()
                InfoRow("Jumlah data", "${formatNumber(datasetSize)} pesan")
                DividerLine()
                InfoRow("Data latih", "${formatNumber(info.trainSize)} pesan")
                DividerLine()
                InfoRow("Data uji", "${formatNumber(info.testSize)} pesan")
                DividerLine()
                InfoRow("Pembagian", "${((1 - testRatio) * 100).toInt()}% latih / ${(testRatio * 100).toInt()}% uji")
                DividerLine()
                InfoRow("Tanggal latih", formatIsoDate(info.trainingDate))
            }
        }

        Spacer(Modifier.height(24.dp))
        SectionLabel("Komposisi Dataset")
        Spacer(Modifier.height(8.dp))
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = MaterialTheme.colorScheme.surface,
            shape = MaterialTheme.shapes.large,
            border = BorderStroke(1.dp, Line),
        ) {
            Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
                InfoRow("Penipuan (spam)", "${formatNumber(info.dataset?.spam)} pesan")
                DividerLine()
                InfoRow("Bukan Penipuan (ham)", "${formatNumber(info.dataset?.ham)} pesan")
                DividerLine()
                InfoRow("Baris mentah", "${formatNumber(info.dataset?.rawSize)} pesan")
            }
        }

        Spacer(Modifier.height(20.dp))
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = TealLight,
            shape = MaterialTheme.shapes.medium,
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "Endpoint API",
                    style = MaterialTheme.typography.labelMedium,
                    color = Teal,
                    fontWeight = FontWeight.Bold,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = BuildConfig.API_BASE_URL,
                    style = MaterialTheme.typography.bodyMedium,
                    color = Ink.copy(alpha = 0.8f),
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    text = "Ubah base URL dengan -PAPI_BASE_URL saat membangun aplikasi.",
                    style = MaterialTheme.typography.labelMedium,
                    color = Muted,
                )
            }
        }
        Spacer(Modifier.height(24.dp))
    }
}

@Composable
private fun MetricTile(label: String, value: String, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier,
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.medium,
        border = BorderStroke(1.dp, Line),
    ) {
        Column(
            modifier = Modifier.padding(vertical = 14.dp, horizontal = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = value,
                style = MaterialTheme.typography.titleMedium,
                color = Ink,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.height(3.dp))
            Text(
                text = label,
                style = MaterialTheme.typography.labelMedium,
                color = Muted,
                textAlign = TextAlign.Center,
            )
        }
    }
}
