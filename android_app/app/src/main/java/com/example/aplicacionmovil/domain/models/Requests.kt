package com.example.aplicacionmovil.domain.models

import com.google.gson.annotations.SerializedName

/**
 * Request de Login
 */
data class LoginRequest(
    @SerializedName("login") val login: String,
    @SerializedName("password") val password: String
)

/**
 * Request de Registro
 */
data class RegisterRequest(
    @SerializedName("name") val name: String,
    @SerializedName("login") val login: String,
    @SerializedName("password") val password: String,
    @SerializedName("telefono") val telefono: String? = null,
    @SerializedName("ubicacion") val ubicacion: String? = null,
    @SerializedName("biografia") val biografia: String? = null
)

/**
 * Request de Creación de Artículo
 */
data class CreateArticleRequest(
    @SerializedName("nombre") val nombre: String,
    @SerializedName("descripcion") val descripcion: String,
    @SerializedName("precio") val precio: Double,
    @SerializedName("estado_producto") val estadoProducto: String,
    @SerializedName("categoria_id") val categoriaId: Int,
    @SerializedName("localidad") val localidad: String? = null,
    @SerializedName("antiguedad") val antiguedad: String? = null,
    @SerializedName("latitud") val latitud: Double? = null,
    @SerializedName("longitud") val longitud: Double? = null,
    @SerializedName("imagenes") val imagenes: List<ImageRequest>? = null,
    @SerializedName("etiquetas_ids") val etiquetasIds: List<Int>? = null
)

/**
 * Request de Imagen para Artículo
 */
data class ImageRequest(
    @SerializedName("image") val image: String, // Base64
    @SerializedName("name") val name: String,
    @SerializedName("sequence") val sequence: Int = 0
)

/**
 * Request de Actualización de Artículo
 */
data class UpdateArticleRequest(
    @SerializedName("nombre") val nombre: String? = null,
    @SerializedName("descripcion") val descripcion: String? = null,
    @SerializedName("precio") val precio: Double? = null,
    @SerializedName("estado_producto") val estadoProducto: String? = null,
    @SerializedName("categoria_id") val categoriaId: Int? = null,
    @SerializedName("localidad") val localidad: String? = null,
    @SerializedName("antiguedad") val antiguedad: String? = null
)

/**
 * Request de Creación de Compra
 */
data class CreatePurchaseRequest(
    @SerializedName("articulo_id") val articuloId: Int,
    @SerializedName("precio") val precio: Double
)

/**
 * Request de Creación de Comentario
 */
data class CreateCommentRequest(
    @SerializedName("articulo_id") val articuloId: Int,
    @SerializedName("texto") val texto: String
)

/**
 * Request de Búsqueda de Artículos
 */
data class SearchArticlesRequest(
    @SerializedName("limit") val limit: Int = 20,
    @SerializedName("offset") val offset: Int = 0,
    @SerializedName("categoria_id") val categoriaId: Int? = null,
    @SerializedName("search") val search: String? = null,
    @SerializedName("precio_min") val precioMin: Double? = null,
    @SerializedName("precio_max") val precioMax: Double? = null,
    @SerializedName("estado_producto") val estadoProducto: String? = null,
    @SerializedName("localidad") val localidad: String? = null
)
