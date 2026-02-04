package com.example.aplicacionmovil.domain.models
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Comment(
    val id: Int,
    val idMensaje: String,
    val idEmisor: Int,
    val nombreEmisor: String,
    val fotoEmisor: String?,
    val idReceptor: Int,
    val nombreReceptor: String,
    val idArticulo: Int,
    val texto: String,
    val fechaHora: String,
    val leido: Boolean = false,
    val activo: Boolean = true
)
