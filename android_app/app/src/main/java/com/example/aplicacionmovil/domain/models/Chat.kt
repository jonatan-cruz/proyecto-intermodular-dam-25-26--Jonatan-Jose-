package com.example.aplicacionmovil.domain.models
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Chat(
    val id: Int,
    val idArticulo: Int,
    val nombreArticulo: String,
    val imagenArticulo: String?,
    val idComprador: Int,
    val nombreComprador: String,
    val fotoComprador: String?,
    val idVendedor: Int,
    val nombreVendedor: String,
    val fotoVendedor: String?,
    val mensajes: List<Message> = emptyList(),
    val ultimoMensaje: String?,
    val fechaUltimoMensaje: String?,
    val activo: Boolean = true
)
@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Message(
    val id: Int,
    val idUsuario: Int,
    val nombreUsuario: String,
    val contenido: String,
    val fechaEnvio: String,
    val leido: Boolean = false,
    val esMio: Boolean = false
)