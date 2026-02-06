package com.example.aplicacionmovil.domain.models
import com.google.gson.annotations.SerializedName
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
    val imagenes: List<ArticleImage>,
    val etiquetas: List<Tag>,
    val comentarios: List<ArticleComment>,
    @SerializedName("conteo_favoritos")
    val conteoFavoritos: Int,
    @SerializedName("conteo_vistas")
    val conteoVistas: Int,
    @SerializedName("create_date")
    val createDate: String? = null
)
data class Category(
    val id: Int,
    val name: String,
    val descripcion: String?,
    val icono: String?,
    val imagen: String?,
    val conteoArticulos: Int
)
data class CategoryDetail(
    val id: Int,
    val nombre: String,
    val descripcion: String? = null
)

data class OwnerDetail(
    val id: Int,
    @SerializedName("id_usuario")
    val idUsuario: String,
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