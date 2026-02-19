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
    @SerializedName("params")  val params: T? = null
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
