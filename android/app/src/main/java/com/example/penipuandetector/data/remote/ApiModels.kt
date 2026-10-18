package com.example.penipuandetector.data.remote

import com.google.gson.annotations.SerializedName

data class PredictRequest(val message: String)

data class PredictResponse(
    val label: String,
    val probabilities: Map<String, Double> = emptyMap(),
    @SerializedName("processed_text") val processedText: String = "",
)

data class ModelInfoResponse(
    val algorithm: String = "-",
    val accuracy: Double = 0.0,
    val vectorizer: String = "-",
    @SerializedName("dataset_size") val datasetSize: Int = 0,
    @SerializedName("train_size") val trainSize: Int = 0,
    @SerializedName("test_size") val testSize: Int = 0,
    @SerializedName("training_date") val trainingDate: String? = null,
    val dataset: DatasetInfo? = null,
    val split: SplitInfo? = null,
    val metrics: MetricsInfo? = null,
)

data class DatasetInfo(
    val name: String? = null,
    val size: Int? = null,
    @SerializedName("raw_size") val rawSize: Int? = null,
    val spam: Int? = null,
    val ham: Int? = null,
)

data class SplitInfo(
    @SerializedName("test_size") val testSize: Double? = null,
    @SerializedName("train_size") val trainSize: Int? = null,
    @SerializedName("test_size_rows") val testSizeRows: Int? = null,
    @SerializedName("random_state") val randomState: Int? = null,
    val stratified: Boolean? = null,
)

data class MetricsInfo(
    val precision: Double? = null,
    val recall: Double? = null,
    val f1: Double? = null,
)

data class HealthResponse(
    val status: String,
    @SerializedName("model_loaded") val modelLoaded: Boolean = false,
)
