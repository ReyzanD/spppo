package com.example.penipuandetector

import android.app.Application
import android.content.Context
import com.example.penipuandetector.data.DetectionRepository
import com.example.penipuandetector.data.local.AppDatabase
import com.example.penipuandetector.data.remote.ApiClient

class AppContainer(context: Context) {
    private val database = AppDatabase.get(context)
    val repository = DetectionRepository(ApiClient.create(), database.detectionDao())
}

class PenipuanApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
