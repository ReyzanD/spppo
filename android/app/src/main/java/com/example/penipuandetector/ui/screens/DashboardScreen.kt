package com.example.penipuandetector.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.ArrowForward
import androidx.compose.material.icons.rounded.ChevronRight
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.rounded.Info
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.penipuandetector.data.local.DetectionEntity
import com.example.penipuandetector.ui.components.SectionLabel
import com.example.penipuandetector.ui.components.StatusPill
import com.example.penipuandetector.ui.formatTimestamp
import com.example.penipuandetector.ui.theme.Amber
import com.example.penipuandetector.ui.theme.Ink
import com.example.penipuandetector.ui.theme.InkSoft
import com.example.penipuandetector.ui.theme.Line
import com.example.penipuandetector.ui.theme.Muted
import com.example.penipuandetector.ui.theme.Paper
import com.example.penipuandetector.ui.theme.Teal
import com.example.penipuandetector.ui.theme.TealLight
import com.example.penipuandetector.ui.viewmodel.DashboardViewModel

@Composable
fun DashboardScreen(
    onDetect: () -> Unit,
    onHistory: () -> Unit,
    onModelInfo: () -> Unit,
    onOpenDetection: (Long) -> Unit,
    viewModel: DashboardViewModel = viewModel(factory = DashboardViewModel.Factory),
) {
    val latest by viewModel.latestDetection.collectAsStateWithLifecycle()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Paper),
        contentPadding = PaddingValues(bottom = 32.dp),
    ) {
        item { DashboardHeader() }

        item {
            PrimaryDetectCard(
                onDetect = onDetect,
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 20.dp),
            )
        }

        item {
            Row(
                modifier = Modifier.padding(horizontal = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                ShortcutCard(
                    title = "Riwayat",
                    subtitle = "Lihat hasil sebelumnya",
                    icon = Icons.Rounded.History,
                    onClick = onHistory,
                    modifier = Modifier.weight(1f),
                )
                ShortcutCard(
                    title = "Info Model",
                    subtitle = "Akurasi & dataset",
                    icon = Icons.Rounded.Info,
                    onClick = onModelInfo,
                    modifier = Modifier.weight(1f),
                )
            }
        }

        item {
            SectionLabel(
                text = "Deteksi Terakhir",
                modifier = Modifier.padding(start = 22.dp, end = 22.dp, top = 28.dp, bottom = 10.dp),
            )
        }

        item {
            if (latest == null) {
                EmptyLatestCard(modifier = Modifier.padding(horizontal = 20.dp))
            } else {
                LatestDetectionCard(
                    detection = latest!!,
                    onClick = { onOpenDetection(latest!!.id) },
                    modifier = Modifier.padding(horizontal = 20.dp),
                )
            }
        }

        item {
            Surface(
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
                color = TealLight,
                shape = MaterialTheme.shapes.medium,
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(
                        imageVector = Icons.Rounded.Info,
                        contentDescription = null,
                        tint = Teal,
                        modifier = Modifier.size(18.dp),
                    )
                    Spacer(Modifier.size(10.dp))
                    Text(
                        text = "Model dilatih pada dataset SMS berbahasa Inggris. Hasil terbaik diperoleh untuk pesan berbahasa Inggris.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Ink.copy(alpha = 0.78f),
                    )
                }
            }
        }
    }
}

@Composable
private fun DashboardHeader() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                brush = Brush.linearGradient(listOf(Ink, InkSoft)),
                shape = RoundedCornerShape(bottomStart = 32.dp, bottomEnd = 32.dp),
            )
            .statusBarsPadding()
            .padding(start = 24.dp, end = 24.dp, top = 10.dp, bottom = 30.dp),
    ) {
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(color = Amber, shape = CircleShape, modifier = Modifier.size(34.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Rounded.Security,
                            contentDescription = null,
                            tint = Ink,
                            modifier = Modifier.size(19.dp),
                        )
                    }
                }
                Spacer(Modifier.size(10.dp))
                Text(
                    text = "DETEKSI PENIPUAN",
                    style = MaterialTheme.typography.labelMedium,
                    color = Amber,
                    fontWeight = FontWeight.Bold,
                )
            }
            Spacer(Modifier.height(20.dp))
            Text(
                text = "Periksa pesan\nsebelum percaya.",
                style = MaterialTheme.typography.headlineMedium,
                color = Color.White,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Tempel pesan SMS atau WhatsApp yang mencurigakan, lalu biarkan model Naive Bayes menganalisisnya.",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.68f),
            )
        }
    }
}

@Composable
private fun PrimaryDetectCard(onDetect: () -> Unit, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.extraLarge,
        shadowElevation = 2.dp,
        border = androidx.compose.foundation.BorderStroke(1.dp, Line),
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(color = TealLight, shape = CircleShape, modifier = Modifier.size(46.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = Icons.Rounded.Search,
                            contentDescription = null,
                            tint = Teal,
                            modifier = Modifier.size(24.dp),
                        )
                    }
                }
                Spacer(Modifier.size(14.dp))
                Column {
                    Text(
                        text = "Deteksi Pesan",
                        style = MaterialTheme.typography.titleMedium,
                        color = Ink,
                    )
                    Text(
                        text = "Analisis teks dengan Multinomial Naive Bayes",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Muted,
                    )
                }
            }
            Spacer(Modifier.height(18.dp))
            Button(
                onClick = onDetect,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = MaterialTheme.shapes.medium,
                colors = ButtonDefaults.buttonColors(containerColor = Teal, contentColor = Color.White),
            ) {
                Text("Mulai Deteksi", fontWeight = FontWeight.Bold)
                Spacer(Modifier.size(8.dp))
                Icon(
                    Icons.AutoMirrored.Rounded.ArrowForward,
                    contentDescription = null,
                    modifier = Modifier.size(18.dp),
                )
            }
        }
    }
}

@Composable
private fun ShortcutCard(
    title: String,
    subtitle: String,
    icon: ImageVector,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.large,
        border = androidx.compose.foundation.BorderStroke(1.dp, Line),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Surface(color = Paper, shape = CircleShape, modifier = Modifier.size(36.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(icon, contentDescription = null, tint = Ink, modifier = Modifier.size(19.dp))
                    }
                }
                Icon(
                    Icons.Rounded.ChevronRight,
                    contentDescription = null,
                    tint = Muted,
                    modifier = Modifier.size(18.dp),
                )
            }
            Spacer(Modifier.height(14.dp))
            Text(title, style = MaterialTheme.typography.titleMedium, color = Ink)
            Spacer(Modifier.height(2.dp))
            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = Muted)
        }
    }
}

@Composable
private fun LatestDetectionCard(
    detection: DetectionEntity,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Surface(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.large,
        border = androidx.compose.foundation.BorderStroke(1.dp, Line),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                StatusPill(isFraud = detection.isFraud, label = detection.label)
                Text(
                    text = formatTimestamp(detection.createdAt),
                    style = MaterialTheme.typography.labelMedium,
                    color = Muted,
                )
            }
            Spacer(Modifier.height(12.dp))
            Text(
                text = detection.message,
                style = MaterialTheme.typography.bodyMedium,
                color = Ink,
                maxLines = 2,
            )
        }
    }
}

@Composable
private fun EmptyLatestCard(modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.large,
        border = androidx.compose.foundation.BorderStroke(1.dp, Line),
    ) {
        Row(
            modifier = Modifier.padding(18.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Surface(color = Paper, shape = CircleShape, modifier = Modifier.size(42.dp)) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.Rounded.History,
                        contentDescription = null,
                        tint = Muted,
                        modifier = Modifier.size(21.dp),
                    )
                }
            }
            Spacer(Modifier.size(14.dp))
            Column {
                Text("Belum ada deteksi", style = MaterialTheme.typography.titleMedium, color = Ink)
                Text(
                    "Hasil deteksi pertama Anda akan muncul di sini.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = Muted,
                )
            }
        }
    }
}
