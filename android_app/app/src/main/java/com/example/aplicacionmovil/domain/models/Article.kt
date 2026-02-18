package com.example.aplicacionmovil.domain.models
import com.google.gson.annotations.SerializedName

/**
 * Modelo de artículo para la lista del Home.
 * Campos mapeados exactamente a lo que devuelve GET /api/v1/articles
 */
data class Article(
    val id: Int,
    val codigo: String,
    val nombre: String,
    val descripcion: String?,
    val precio: Float,

    @SerializedName("estado_producto")
    val estadoProducto: String,

    // La lista de artículos no devuelve estado_publicacion, se pone valor por defecto
    @SerializedName("estado_publicacion")
    val estadoPublicacion: String = "publicado",

    val antiguedad: Int = 0,
    val localidad: String? = null,
    val latitud: Double? = null,
    val longitud: Double? = null,

    // La API devuelve un objeto "categoria" con "id" y "nombre"
    val categoria: Category? = null,

    // La API devuelve un objeto "propietario"
    val propietario: ArticlePropietario? = null,

    // La API devuelve "imagen_principal" como string (base64 o URL), no una lista
    @SerializedName("imagen_principal")
    val imagenPrincipal: String? = null,

    @SerializedName("conteo_imagenes")
    val conteoImagenes: Int = 0,

    @SerializedName("conteo_favoritos")
    val conteoFavoritos: Int = 0,

    @SerializedName("conteo_vistas")
    val conteoVistas: Int = 0,

    val etiquetas: List<ArticleTag> = emptyList(),

    @SerializedName("create_date")
    val createDate: String? = null
)

/**
 * Propietario del artículo (tal como viene en la lista de artículos)
 */
data class ArticlePropietario(
    val id: Int,
    val nombre: String,
    @SerializedName("calificacion_promedio")
    val calificacionPromedio: Double? = null
)

/**
 * Categoría del artículo
 * La API devuelve "nombre" (no "name") en el contexto de artículos
 */
data class Category(
    val id: Int,
    // En la lista de artículos la API devuelve "nombre"
    // En el endpoint de categorías puede devolver "name"
    val nombre: String? = null,
    val name: String? = null,
    val descripcion: String? = null,
    val icono: String? = null,
    val imagen: String? = null,
    @SerializedName("conteo_articulos")
    val conteoArticulos: Int = 0
) {
    // Nombre unificado para usar en la UI independientemente del campo que venga
    val displayName: String get() = nombre ?: name ?: ""
}

/**
 * Etiqueta de artículo
 */
data class ArticleTag(
    val id: Int,
    val nombre: String,
    val color: String? = null
)

// ==================== DETALLE DE ARTÍCULO ====================

data class ArticleDetail(
    val id: Int,
    val codigo: String,
    val nombre: String,
    val descripcion: String,
    val precio: Double,
    @SerializedName("estado_producto")
    val estadoProducto: String,
    @SerializedName("estado_publicacion")
    val estadoPublicacion: String,
    val antiguedad: String? = null,
    val localidad: String? = null,
    val latitud: Double? = null,
    val longitud: Double? = null,
    val categoria: CategoryDetail? = null,
    val propietario: OwnerDetail? = null,
    val imagenes: List<ArticleImage> = emptyList(),
    val etiquetas: List<Tag> = emptyList(),
    val comentarios: List<ArticleComment> = emptyList(),
    @SerializedName("conteo_favoritos")
    val conteoFavoritos: Int = 0,
    @SerializedName("conteo_vistas")
    val conteoVistas: Int = 0,
    @SerializedName("conteo_comentarios")
    val conteoComentarios: Int = 0,
    @SerializedName("create_date")
    val createDate: String? = null
)

data class CategoryDetail(
    val id: Int,
    val nombre: String,
    val descripcion: String? = null
)

data class OwnerDetail(
    val id: Int,
    @SerializedName("id_usuario")
    val idUsuario: String? = null,
    val nombre: String,
    @SerializedName("calificacion_promedio")
    val calificacionPromedio: Double? = null,
    @SerializedName("total_valoraciones")
    val totalValoraciones: Int? = null,
    @SerializedName("productos_vendidos")
    val productosVendidos: Int? = null,
    val antiguedad: String? = null
)

data class ArticleImage(
    val id: Int,
    val name: String,
    val image: String?, // Base64
    val sequence: Int
)

data class ArticleComment(
    val id: Int,
    val texto: String,
    val emisor: CommentUser,
    @SerializedName("fecha_hora")
    val fechaHora: String? = null
)

data class CommentUser(
    val id: Int,
    val nombre: String
)

data class Tag(
    val id: Int,
    val nombre: String,
    val color: String? = null
)