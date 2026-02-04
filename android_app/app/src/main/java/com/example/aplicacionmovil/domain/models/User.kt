package com.example.aplicacionmovil.domain.models
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class User(

    val id: Int,
    val name: String,
    val email: String,
    val telefono: String?,
    val fotoPerfil: String?, // URL o base64
    val ciudad: String?,
    val calificacionPromedio: Float = 0f,
    val numeroVentas: Int = 0,
    val numeroCompras: Int = 0,
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
