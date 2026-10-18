package com.example.penipuandetector.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.example.penipuandetector.PenipuanApplication
import com.example.penipuandetector.data.DetectionRepository
import com.example.penipuandetector.data.local.DetectionEntity
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn

class DashboardViewModel(repository: DetectionRepository) : ViewModel() {
    val latestDetection: StateFlow<DetectionEntity?> = repository.latest()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = null,
        )

    companion object {
        val Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as PenipuanApplication
                DashboardViewModel(app.container.repository)
            }
        }
    }
}
