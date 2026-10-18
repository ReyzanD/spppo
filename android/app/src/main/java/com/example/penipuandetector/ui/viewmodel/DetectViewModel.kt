package com.example.penipuandetector.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.example.penipuandetector.PenipuanApplication
import com.example.penipuandetector.data.DetectionRepository
import com.example.penipuandetector.data.remote.toUserMessage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

const val MAX_MESSAGE_LENGTH = 1000

data class DetectUiState(
    val message: String = "",
    val isLoading: Boolean = false,
    val error: String? = null,
    val savedDetectionId: Long? = null,
)

class DetectViewModel(private val repository: DetectionRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(DetectUiState())
    val uiState: StateFlow<DetectUiState> = _uiState.asStateFlow()

    fun onMessageChange(value: String) {
        if (value.length <= MAX_MESSAGE_LENGTH) {
            _uiState.update { it.copy(message = value, error = null) }
        }
    }

    fun detect() {
        val message = _uiState.value.message.trim()
        if (message.isEmpty()) {
            _uiState.update { it.copy(error = "Pesan tidak boleh kosong.") }
            return
        }
        if (_uiState.value.isLoading) return

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null, savedDetectionId = null) }
            repository.detect(message)
                .onSuccess { detection ->
                    _uiState.update {
                        it.copy(isLoading = false, savedDetectionId = detection.id)
                    }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(isLoading = false, error = error.toUserMessage())
                    }
                }
        }
    }

    fun consumeNavigation() {
        _uiState.update { it.copy(savedDetectionId = null) }
    }

    companion object {
        val Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as PenipuanApplication
                DetectViewModel(app.container.repository)
            }
        }
    }
}
