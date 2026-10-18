package com.example.penipuandetector.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface DetectionDao {
    @Query("SELECT * FROM detections ORDER BY createdAt DESC")
    fun observeAll(): Flow<List<DetectionEntity>>

    @Query("SELECT * FROM detections ORDER BY createdAt DESC LIMIT 1")
    fun observeLatest(): Flow<DetectionEntity?>

    @Query("SELECT * FROM detections WHERE id = :id")
    fun observeById(id: Long): Flow<DetectionEntity?>

    @Insert
    suspend fun insert(detection: DetectionEntity): Long

    @Query("DELETE FROM detections WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("DELETE FROM detections")
    suspend fun clearAll()
}
