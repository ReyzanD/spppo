package com.example.penipuandetector.data

import com.example.penipuandetector.data.local.DetectionDao
import com.example.penipuandetector.data.local.DetectionEntity
import com.example.penipuandetector.data.remote.ApiService
import com.example.penipuandetector.data.remote.ModelInfoResponse
import com.example.penipuandetector.data.remote.PredictRequest
import kotlinx.coroutines.flow.Flow

class DetectionRepository(
    private val api: ApiService,
    private val dao: DetectionDao,
) {
    fun history(): Flow<List<DetectionEntity>> = dao.observeAll()

    fun latest(): Flow<DetectionEntity?> = dao.observeLatest()

    fun findById(id: Long): Flow<DetectionEntity?> = dao.observeById(id)

    /** Classify a message and persist the result as history. */
    suspend fun detect(message: String): Result<DetectionEntity> = runCatching {
        val response = api.predict(PredictRequest(message))
        val entity = DetectionEntity(
            message = message,
            label = response.label,
            probabilityFraud = response.probabilities["Penipuan"] ?: 0.0,
            probabilityHam = response.probabilities["Bukan Penipuan"] ?: 0.0,
            processedText = response.processedText,
        )
        val id = dao.insert(entity)
        entity.copy(id = id)
    }

    suspend fun modelInfo(): Result<ModelInfoResponse> = runCatching { api.modelInfo() }

    suspend fun delete(id: Long) = dao.deleteById(id)

    suspend fun clearAll() = dao.clearAll()
}
