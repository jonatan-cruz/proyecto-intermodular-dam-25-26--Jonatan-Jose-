package com.example.aplicacionmovil.domain.models
import com.google.gson.annotations.SerializedName

// ==================== RESPUESTA BASE ====================

/**
 * Clase genérica para todas las respuestas de la API
 */
data class ApiResponse<T>(
    @SerializedName("success")
    val success: Boolean,

    @SerializedName("message")
    val message: String? = null,

    @SerializedName("data")
    val data: T? = null,

    @SerializedName("error_code")
    val errorCode: String? = null
)

data class AuthResponse(
    @SerializedName("token")
    val token: String,

    @SerializedName("user")
    val user: User,

    @SerializedName("expires_in")
    val expiresIn: Int
)

