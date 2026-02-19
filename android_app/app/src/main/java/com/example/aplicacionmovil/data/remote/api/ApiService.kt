package com.example.aplicacionmovil.data.remote.api

import com.example.aplicacionmovil.domain.models.CreateArticleRequest
import com.example.aplicacionmovil.domain.models.CreateCommentRequest
import com.example.aplicacionmovil.domain.models.CreatePurchaseRequest
import com.example.aplicacionmovil.domain.models.LoginRequest
import com.example.aplicacionmovil.domain.models.RegisterRequest
import com.example.aplicacionmovil.domain.models.SearchArticlesRequest
import com.example.aplicacionmovil.domain.models.UpdateArticleRequest
import com.example.aplicacionmovil.domain.models.*
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import retrofit2.Response
import retrofit2.http.*

/**
 * Interface del servicio API
 * Define todos los endpoints de la API REST de Second Market
 */
interface ApiService {
    
    // ==================== AUTH ENDPOINTS ====================

    @POST("api/v1/auth/login")
    suspend fun login(@Body request: JsonRpcRequest<LoginRequest>): Response<JsonRpcResponse<ApiResponse<AuthResponse>>>
    
    @POST("api/v1/auth/register")
    suspend fun register(@Body request: JsonRpcRequest<RegisterRequest>): Response<JsonRpcResponse<ApiResponse<AuthResponse>>>
    
    @POST("api/v1/auth/verify")
    suspend fun verifyToken(@Body body: JsonRpcRequest<Unit> = JsonRpcRequest()): Response<JsonRpcResponse<ApiResponse<Map<String, User>>>>
    
    @POST("api/v1/auth/logout")
    suspend fun logout(@Body body: JsonRpcRequest<Unit> = JsonRpcRequest()): Response<JsonRpcResponse<ApiResponse<Any>>>
    
    // ==================== ARTICLES ENDPOINTS ====================

    /**
     * Obtener lista de artículos publicados
     */
    @POST("api/v1/articles/list")
    suspend fun getArticles(@Body request: JsonRpcRequest<SearchArticlesRequest>): Response<JsonRpcResponse<ApiResponse<ArticlesResponse>>>

    /**
     * Obtener detalle de un artículo
     */
    @POST("api/v1/articles/{id}")
    suspend fun getArticleDetail(@Path("id") articleId: Int, @Body body: JsonRpcRequest<Unit> = JsonRpcRequest()): Response<JsonRpcResponse<ApiResponse<ArticleDetail>>>
    
    /**
     * Crear un nuevo artículo
     */
    @POST("api/v1/articles")
    suspend fun createArticle(@Body request: JsonRpcRequest<CreateArticleRequest>): Response<JsonRpcResponse<ApiResponse<Map<String, Any>>>>
    
    /**
     * Actualizar un artículo
     */
    @HTTP(method = "PUT", path = "api/v1/articles/{id}", hasBody = true)
    suspend fun updateArticle(
        @Path("id") articleId: Int,
        @Body request: JsonRpcRequest<UpdateArticleRequest>
    ): Response<JsonRpcResponse<ApiResponse<Any>>>
    
    /**
     * Publicar un artículo
     */
    @POST("api/v1/articles/{id}/publish")
    suspend fun publishArticle(@Path("id") articleId: Int, @Body body: JsonRpcRequest<Unit> = JsonRpcRequest()): Response<JsonRpcResponse<ApiResponse<Any>>>
    
    /**
     * Eliminar un artículo
     */
    @HTTP(method = "DELETE", path = "api/v1/articles/{id}")
    suspend fun deleteArticle(@Path("id") articleId: Int): Response<JsonRpcResponse<ApiResponse<Any>>>
    
    /**
     * Obtener mis artículos
     */
    @POST("api/v1/articles/my-articles")
    suspend fun getMyArticles(@Body request: JsonRpcRequest<Map<String, Int>>): Response<JsonRpcResponse<ApiResponse<ArticlesResponse>>>

    // ==================== PURCHASES ENDPOINTS ====================

    /**
     * Crear una compra
     */
    @POST("api/v1/purchases")
    suspend fun createPurchase(@Body request: JsonRpcRequest<CreatePurchaseRequest>): Response<JsonRpcResponse<ApiResponse<PurchaseResponse>>>

    /**
     * Obtener mis compras
     */
    @GET("api/v1/purchases/my-purchases")
    suspend fun getMyPurchases(): Response<JsonRpcResponse<ApiResponse<PurchasesResponse>>>

    /**
     * Obtener mis ventas
     */
    @GET("api/v1/purchases/my-sales")
    suspend fun getMySales(): Response<JsonRpcResponse<ApiResponse<SalesResponse>>>

    // ==================== COMMENTS ENDPOINTS ====================
    
    /**
     * Crear un comentario
     */
    @POST("api/v1/comments")
    suspend fun createComment(@Body request: JsonRpcRequest<CreateCommentRequest>): Response<JsonRpcResponse<ApiResponse<Map<String, Any>>>>
    
    /**
     * Eliminar un comentario
     */
    @HTTP(method = "DELETE", path = "api/v1/comments/{id}")
    suspend fun deleteComment(@Path("id") commentId: Int): Response<JsonRpcResponse<ApiResponse<Any>>>
    
    // ==================== CATEGORIES ENDPOINTS ====================
    
    /**
     * Obtener todas las categorías
     */
    @POST("api/v1/categories")
    suspend fun getCategories(@Body body: JsonRpcRequest<Unit> = JsonRpcRequest()): Response<JsonRpcResponse<ApiResponse<Map<String, List<Category>>>>>
}
