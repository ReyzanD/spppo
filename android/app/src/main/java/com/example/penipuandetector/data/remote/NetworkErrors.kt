package com.example.penipuandetector.data.remote

import retrofit2.HttpException
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

/** Turn low-level failures into messages the app can show as-is. */
fun Throwable.toUserMessage(): String = when (this) {
    is UnknownHostException, is ConnectException, is SocketTimeoutException, is IOException ->
        "Tidak dapat terhubung ke server. Periksa koneksi internet dan pastikan API berjalan."
    is HttpException -> when (code()) {
        422 -> "Pesan tidak valid. Periksa kembali teks yang dimasukkan."
        503 -> "Model belum tersedia di server. Jalankan proses pelatihan model terlebih dahulu."
        in 500..599 -> "Server mengalami kesalahan (${code()}). Silakan coba lagi."
        else -> "Permintaan ditolak oleh server (${code()})."
    }
    else -> message?.let { "Terjadi kesalahan: $it" } ?: "Terjadi kesalahan yang tidak diketahui."
}
