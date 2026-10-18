package com.example.penipuandetector.data.remote

import com.example.penipuandetector.BuildConfig
import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import java.util.concurrent.TimeUnit

interface ApiService {
    @POST("predict")
    suspend fun predict(@Body request: PredictRequest): PredictResponse

    @GET("model-info")
    suspend fun modelInfo(): ModelInfoResponse

    @GET("health")
    suspend fun health(): HealthResponse
}

object ApiClient {
    /**
     * The base URL comes from BuildConfig, so it can be changed without touching
     * code: `./gradlew assembleDebug -PAPI_BASE_URL=http://192.168.1.10:8000/`.
     */
    fun create(baseUrl: String = BuildConfig.API_BASE_URL): ApiService {
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BASIC
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(logging)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()

        val gson = GsonBuilder().setLenient().create()

        return Retrofit.Builder()
            .baseUrl(normalizeBaseUrl(baseUrl))
            .client(client)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
            .create(ApiService::class.java)
    }

    private fun normalizeBaseUrl(value: String): String {
        val trimmed = value.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }
}
