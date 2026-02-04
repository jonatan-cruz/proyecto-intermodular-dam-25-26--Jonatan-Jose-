package com.example.aplicacionmovil.domain.models
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Report(
    val id: Int,
    val numDenuncia: String,
    val motivo: String,
    val descripcion: String,
    val tipoDenuncia: String,
    val estado: String,
    val fechaCreacion: String,
    val itemDenunciado: String,
    val idItemDenunciado: Int
)
