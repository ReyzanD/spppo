package com.example.penipuandetector.ui.viewmodel

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.createSavedStateHandle
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.example.penipuandetector.PenipuanApplication
import com.example.penipuandetector.data.DetectionRepository
import com.example.penipuandetector.data.local.DetectionEntity
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

data class ResultUiState(
    val isLoading: Boolean = true,
    val detection: DetectionEntity? = null,
)

class ResultViewModel(
    repository: DetectionRepository,
    savedStateHandle: SavedStateHandle,
) : ViewModel() {
    private val detectionId: Long = savedStateHandle["id"] ?: 0L

    val uiState: StateFlow<ResultUiState> = repository.findById(detectionId)
        .map { ResultUiState(isLoading = false, detection = it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ResultUiState(),
        )

    companion object {
        val Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as PenipuanApplication
                ResultViewModel(app.container.repository, createSavedStateHandle())
            }
        }
    }
}
