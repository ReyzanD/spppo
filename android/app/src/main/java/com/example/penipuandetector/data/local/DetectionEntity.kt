package com.example.penipuandetector.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "detections")
data class DetectionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val message: String,
    val label: String,
    val probabilityFraud: Double,
    val probabilityHam: Double,
    val processedText: String,
    val createdAt: Long = System.currentTimeMillis(),
) {
    val isFraud: Boolean
        get() = label.equals("Penipuan", ignoreCase = true)
}
