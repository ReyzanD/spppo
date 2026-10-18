package com.example.penipuandetector.ui.screens

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Delete
import androidx.compose.material.icons.rounded.DeleteSweep
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.penipuandetector.data.local.DetectionEntity
import com.example.penipuandetector.ui.components.ScreenHeader
import com.example.penipuandetector.ui.asPercent
import com.example.penipuandetector.ui.components.StatusPill
import com.example.penipuandetector.ui.formatTimestamp
import com.example.penipuandetector.ui.theme.Danger
import com.example.penipuandetector.ui.theme.Ink
import com.example.penipuandetector.ui.theme.Line
import com.example.penipuandetector.ui.theme.Muted
import com.example.penipuandetector.ui.theme.Paper
import com.example.penipuandetector.ui.theme.Teal
import com.example.penipuandetector.ui.viewmodel.HistoryViewModel

@Composable
fun HistoryScreen(
    onBack: () -> Unit,
    onDetect: () -> Unit,
    viewModel: HistoryViewModel = viewModel(factory = HistoryViewModel.Factory),
) {
    val items by viewModel.items.collectAsStateWithLifecycle()
    var showClearDialog by rememberSaveable { mutableStateOf(false) }

    Scaffold(
        topBar = {
            ScreenHeader(
                title = "Riwayat Deteksi",
                onBack = onBack,
                actions = {
                    if (items.isNotEmpty()) {
                        IconButton(onClick = { showClearDialog = true }) {
                            Icon(
                                Icons.Rounded.DeleteSweep,
                                contentDescription = "Hapus semua riwayat",
                                tint = Danger,
                            )
                        }
                    }
                },
            )
        },
    ) { innerPadding ->
        if (items.isEmpty()) {
            EmptyHistory(
                onDetect = onDetect,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding),
                contentPadding = PaddingValues(horizontal = 20.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                item {
                    Text(
                        text = "${items.size} deteksi tersimpan di perangkat ini",
                        style = MaterialTheme.typography.bodyMedium,
                        color = Muted,
                        modifier = Modifier.padding(bottom = 4.dp),
                    )
                }
                items(items, key = { it.id }) { detection ->
                    HistoryCard(
                        detection = detection,
                        onDelete = { viewModel.delete(detection.id) },
                    )
                }
            }
        }
    }

    if (showClearDialog) {
        AlertDialog(
            onDismissRequest = { showClearDialog = false },
            title = { Text("Hapus semua riwayat?") },
            text = { Text("Seluruh ${items.size} hasil deteksi akan dihapus dari perangkat ini. Tindakan ini tidak dapat dibatalkan.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.clearAll()
                        showClearDialog = false
                    },
                ) {
                    Text("Hapus semua", color = Danger, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showClearDialog = false }) {
                    Text("Batal")
                }
            },
        )
    }
}

@Composable
private fun HistoryCard(detection: DetectionEntity, onDelete: () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        color = MaterialTheme.colorScheme.surface,
        shape = MaterialTheme.shapes.large,
        border = BorderStroke(1.dp, Line),
    ) {
        Column(modifier = Modifier.padding(start = 16.dp, top = 14.dp, end = 8.dp, bottom = 14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                StatusPill(isFraud = detection.isFraud, label = detection.label)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = formatTimestamp(detection.createdAt),
                        style = MaterialTheme.typography.labelMedium,
                        color = Muted,
                    )
                    IconButton(onClick = onDelete, modifier = Modifier.size(36.dp)) {
                        Icon(
                            Icons.Rounded.Delete,
                            contentDescription = "Hapus riwayat ini",
                            tint = Muted,
                            modifier = Modifier.size(19.dp),
                        )
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            Text(
                text = detection.message,
                style = MaterialTheme.typography.bodyMedium,
                color = Ink,
                maxLines = 3,
                modifier = Modifier.padding(end = 8.dp),
            )
            Spacer(Modifier.height(10.dp))
            Text(
                text = "Penipuan ${detection.probabilityFraud.asPercent()}  ·  " +
                    "Bukan Penipuan ${detection.probabilityHam.asPercent()}",
                style = MaterialTheme.typography.labelMedium,
                color = Muted,
            )
        }
    }
}

@Composable
private fun EmptyHistory(onDetect: () -> Unit, modifier: Modifier = Modifier) {
    Box(modifier = modifier.padding(28.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Surface(
                color = Paper,
                shape = CircleShape,
                modifier = Modifier.size(84.dp),
                border = BorderStroke(1.dp, Line),
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        Icons.Rounded.History,
                        contentDescription = null,
                        tint = Muted,
                        modifier = Modifier.size(38.dp),
                    )
                }
            }
            Spacer(Modifier.height(20.dp))
            Text(
                text = "Belum ada riwayat",
                style = MaterialTheme.typography.titleLarge,
                color = Ink,
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                text = "Hasil deteksi yang Anda lakukan akan tersimpan otomatis di sini.",
                style = MaterialTheme.typography.bodyMedium,
                color = Muted,
                textAlign = TextAlign.Center,
            )
            Spacer(Modifier.height(20.dp))
            Button(
                onClick = onDetect,
                shape = MaterialTheme.shapes.medium,
                colors = ButtonDefaults.buttonColors(containerColor = Teal, contentColor = Color.White),
            ) {
                Icon(Icons.Rounded.Search, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.size(8.dp))
                Text("Deteksi Sekarang", fontWeight = FontWeight.Bold)
            }
        }
    }
}
