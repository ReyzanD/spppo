package com.example.penipuandetector.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider.AndroidViewModelFactory.Companion.APPLICATION_KEY
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.example.penipuandetector.PenipuanApplication
import com.example.penipuandetector.data.DetectionRepository
import com.example.penipuandetector.data.remote.ModelInfoResponse
import com.example.penipuandetector.data.remote.toUserMessage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ModelInfoUiState(
    val isLoading: Boolean = true,
    val info: ModelInfoResponse? = null,
    val error: String? = null,
)

class ModelInfoViewModel(private val repository: DetectionRepository) : ViewModel() {
    private val _uiState = MutableStateFlow(ModelInfoUiState())
    val uiState: StateFlow<ModelInfoUiState> = _uiState.asStateFlow()

    init {
        load()
    }

    fun load() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            repository.modelInfo()
                .onSuccess { info ->
                    _uiState.update { it.copy(isLoading = false, info = info) }
                }
                .onFailure { error ->
                    _uiState.update {
                        it.copy(isLoading = false, error = error.toUserMessage())
                    }
                }
        }
    }

    companion object {
        val Factory = viewModelFactory {
            initializer {
                val app = this[APPLICATION_KEY] as PenipuanApplication
                ModelInfoViewModel(app.container.repository)
            }
        }
    }
}
