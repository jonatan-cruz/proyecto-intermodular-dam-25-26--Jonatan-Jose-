package com.example.aplicacionmovil.domain.models
import kotlinx.serialization.Serializable

@OptIn(kotlinx.serialization.InternalSerializationApi::class)
@Serializable
data class Article(
    val id: Int,
    val codigo: String,
    val nombre: String,
    val descripcion: String?,
    val precio: Float,
    val estadoProducto: String,
    val estadoPublicacion: String,
    val antiguedad: Int,
    val localidad: String,
    val latitud: Double?,
    val longitud: Double?,
    val idPropietario: Int,
    val nombrePropietario: String,
    val fotoPropietario: String?,
    val categoria: Category,
    val imagenes: List<String>,
    val etiquetas: List<String>,
    val conteoVistas: Int = 0,
    val conteoChats: Int = 0,
    val conteoComentarios: Int = 0,
    val activo: Boolean = true,
    val fechaCreacion: String
)
data class Category(
    val id: Int,
    val name: String,
    val descripcion: String?,
    val icono: String?,
    val imagen: String?,
    val conteoArticulos: Int
)