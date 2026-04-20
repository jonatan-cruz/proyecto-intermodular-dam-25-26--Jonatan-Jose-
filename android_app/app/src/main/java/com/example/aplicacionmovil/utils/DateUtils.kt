package com.example.aplicacionmovil.utils

import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone

object DateUtils {
    
    private val isoFormats = listOf(
        SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSSSS", Locale.getDefault()).apply { timeZone = TimeZone.getTimeZone("UTC") },
        SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault()).apply { timeZone = TimeZone.getTimeZone("UTC") },
        SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSSSSS", Locale.getDefault()).apply { timeZone = TimeZone.getTimeZone("UTC") },
        SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).apply { timeZone = TimeZone.getTimeZone("UTC") },
        SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).apply { timeZone = TimeZone.getTimeZone("UTC") }
    )

    fun parseDate(dateString: String?): Date? {
        if (dateString.isNullOrBlank()) return null
        
        for (format in isoFormats) {
            try {
                return format.parse(dateString)
            } catch (e: Exception) {
                // Ignore and try the next one
            }
        }
        return null
    }

    /**
     * Devuelve una fecha en formato: "12 de marzo de 2026"
     */
    fun formatLongDate(dateString: String?): String {
        val date = parseDate(dateString) ?: return dateString ?: ""
        val formatter = SimpleDateFormat("dd 'de' MMMM 'de' yyyy", Locale("es", "ES"))
        return formatter.format(date)
    }

    /**
     * Devuelve formato relativo: "Hace 2 h", "Ayer", "12/03/2026"
     */
    fun formatRelativeTime(dateString: String?): String {
        val date = parseDate(dateString) ?: return dateString ?: ""
        
        val now = Calendar.getInstance()
        val time = Calendar.getInstance().apply { time = date }
        
        val diff = now.timeInMillis - time.timeInMillis
        
        val seconds = diff / 1000
        val minutes = seconds / 60
        val hours = minutes / 60
        val days = hours / 24
        
        return when {
            diff < 0 -> "Ahora" 
            seconds < 60 -> "Hace unos segundos"
            minutes < 60 -> "Hace $minutes min"
            hours < 24 -> "Hace $hours h"
            days == 1L -> "Ayer"
            days in 2..7 -> "Hace $days días"
            else -> {
                val formatter = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
                formatter.format(date)
            }
        }
    }

    /**
     * Formato para chats: Si es hoy, muestra la hora (Ej. 14:30), si no "dd/MM/yyyy"
     */
    fun formatChatTime(dateString: String?): String {
        val date = parseDate(dateString) ?: return dateString ?: ""
        
        val now = Calendar.getInstance()
        val time = Calendar.getInstance().apply { time = date }
        
        return if (now.get(Calendar.YEAR) == time.get(Calendar.YEAR) &&
            now.get(Calendar.DAY_OF_YEAR) == time.get(Calendar.DAY_OF_YEAR)) {
            SimpleDateFormat("HH:mm", Locale.getDefault()).format(date)
        } else {
            SimpleDateFormat("dd/MM/yyyy", Locale.getDefault()).format(date)
        }
    }
}
