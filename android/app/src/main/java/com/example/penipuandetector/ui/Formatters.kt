package com.example.penipuandetector.ui

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

private val indonesian: Locale = Locale("id", "ID")

/** Format a probability (0..1) as an Indonesian percentage string. */
fun Double.asPercent(decimals: Int = 1): String =
    String.format(indonesian, "%.${decimals}f%%", this * 100)

/** Format a Room timestamp for the history list. */
fun formatTimestamp(epochMillis: Long): String {
    val formatter = DateTimeFormatter.ofPattern("dd MMM yyyy, HH:mm", indonesian)
    return Instant.ofEpochMilli(epochMillis)
        .atZone(ZoneId.systemDefault())
        .format(formatter)
}

/** Format the ISO training date from metadata, falling back to the raw value. */
fun formatIsoDate(value: String?): String {
    if (value.isNullOrBlank()) return "-"
    return runCatching {
        val formatter = DateTimeFormatter.ofPattern("dd MMM yyyy, HH:mm", indonesian)
        Instant.parse(value).atZone(ZoneId.systemDefault()).format(formatter)
    }.getOrDefault(value)
}

/** Group thousands the way Indonesian readers expect: 5.171. */
fun formatNumber(value: Int?): String {
    if (value == null) return "-"
    return String.format(indonesian, "%,d", value).replace(',', '.')
}
