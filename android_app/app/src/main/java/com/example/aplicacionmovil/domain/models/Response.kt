package com.example.aplicacionmovil.domain.models
import com.google.gson.annotations.SerializedName

// ==================== PETICIÓN JSON-RPC ====================

/**
 * Envoltorio JSON-RPC 2.0 para peticiones al servidor Odoo.
 * Odoo con type='json' lee los datos del campo "params".
 * Uso sin datos: JsonRpcRequest()
 * Uso con datos: JsonRpcRequest(params = miRequest)
 */
data class JsonRpcRequest<T : Any>(
    @SerializedName("jsonrpc") val jsonrpc: String = "2.0",
    @SerializedName("method")  val method: String  = "call",
    @SerializedName("params")  val params: T = mapOf<String, Any>() as T
)

// ==================== RESPUESTA BASE ====================

/**
 * Envoltorio para el protocolo JSON-RPC 2.0 que usa el servidor
 */
data class JsonRpcResponse<T>(
    @SerializedName("jsonrpc")
    val jsonrpc: String,
    
    @SerializedName("id")
    val id: Any? = null,
    
    @SerializedName("result")
    val result: T
)

/**
 * Clase genérica para el contenido de la respuesta (dentro de "result")
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

data class ArticlesResponse(
    val articles: List<Article>,
    val total: Int,
    val limit: Int,
    val offset: Int
)

data class PurchaseResponse(
    @SerializedName("purchase_id")
    val purchaseId: Int,
    @SerializedName("id_compra")
    val idCompra: String
)

data class PurchasesResponse(
    val purchases: List<Purchase>
)

data class SalesResponse(
    val sales: List<Sale>
)

// ==================== CHAT RESPONSES ====================

data class ChatsResponse(
    val chats: List<ChatConversation>
)

data class ChatMessagesResponse(
    val messages: List<ChatMessage>,
    @SerializedName("chat_info")
    val chatInfo: ChatInfo?
)

data class ChatInfo(
    val articulo: ChatArticuloInfo?
)

data class ChatArticuloInfo(
    val id: Int,
    val nombre: String?
)

/**
 * Representa una conversación de chat
 * Estructura según el backend de Odoo
 */
data class ChatConversation(
    @SerializedName("id")
    val id: Int,
    @SerializedName("articulo")
    val articulo: ChatArticulo?,
    @SerializedName("otro_usuario")
    val otroUsuario: ChatUsuario?,
    @SerializedName("ultimo_mensaje")
    val ultimoMensaje: String?,
    @SerializedName("fecha_ultimo_mensaje")
    val fechaUltimoMensaje: String?,
    @SerializedName("conteo_mensajes")
    val conteoMensajes: Int = 0
)

data class ChatArticulo(
    val id: Int,
    val nombre: String?,
    val precio: Double?
)

data class ChatUsuario(
    val id: Int,
    val nombre: String?
)

/**
 * Representa un mensaje individual de chat
 * Estructura según el backend de Odoo
 */
data class ChatMessage(
    @SerializedName("id")
    val id: Int,
    @SerializedName("contenido")
    val contenido: String,
    @SerializedName("fecha_envio")
    val fechaEnvio: String?,
    @SerializedName("leido")
    val leido: Boolean = false,
    @SerializedName("usuario")
    val usuario: ChatUsuario?,
    @SerializedName("is_mine")
    val isMine: Boolean = false
)
