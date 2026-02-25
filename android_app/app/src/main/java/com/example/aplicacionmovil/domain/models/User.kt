package com.example.aplicacionmovil.domain.models

import com.google.gson.annotations.SerializedName
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class User(
    val id: Int,
    val name: String,
    @SerializedName("login")
    val email: String,
    @SerializedName("avatar")
    val fotoPerfil: String?, // URL o base64
    @SerializedName("ubicacion")
    val ciudad: String?,
    @SerializedName("biografia")
    val biografia: String?,
    @SerializedName("telefono")
    val telefono: String?,
    @SerializedName("calificacion_promedio")
    val calificacionPromedio: Float = 0f,
    @SerializedName("productos_vendidos")
    val numeroVentas: Int = 0,
    @SerializedName("productos_comprados")
    val numeroCompras: Int = 0,
    @SerializedName("fecha_registro")
    val fechaRegistro: String,
    val activo: Boolean = true,
    val ratings: List<Rating> = emptyList()
)
@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Rating(
    val id: Int,
    val calificacion: Int, // 1-5
    val comentario: String?,
    val nombreValorador: String,
    val fechaHora: String
)
