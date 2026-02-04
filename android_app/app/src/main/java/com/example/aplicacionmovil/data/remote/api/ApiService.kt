package com.example.secondmarket.data.api

import com.example.secondmarket.data.model.*
import com.example.secondmarket.data.model.requests.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Interface del servicio API
 * Define todos los endpoints de la API REST de Second Market
 */
interface ApiService {
    
    // ==================== AUTH ENDPOINTS ====================
    
    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<ApiResponse<AuthResponse>>
    
    @POST("api/v1/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<ApiResponse<AuthResponse>>
    
    @POST("api/v1/auth/verify")
    suspend fun verifyToken(): Response<ApiResponse<Map<String, User>>>
    
    @POST("api/v1/auth/logout")
    suspend fun logout(): Response<ApiResponse<Any>>
    
    // ==================== ARTICLES ENDPOINTS ====================
    
    /**
     * Obtener lista de artículos publicados
     */
    @POST("api/v1/articles")
    suspend fun getArticles(@Body request: SearchArticlesRequest): Response<ApiResponse<ArticlesResponse>>
    
    /**
     * Obtener detalle de un artículo
     */
    @POST("api/v1/articles/{id}")
    suspend fun getArticleDetail(@Path("id") articleId: Int): Response<ApiResponse<ArticleDetail>>
    
    /**
     * Crear un nuevo artículo
     */
    @POST("api/v1/articles")
    suspend fun createArticle(@Body request: CreateArticleRequest): Response<ApiResponse<Map<String, Any>>>
    
    /**
     * Actualizar un artículo
     */
    @HTTP(method = "PUT", path = "api/v1/articles/{id}", hasBody = true)
    suspend fun updateArticle(
        @Path("id") articleId: Int,
        @Body request: UpdateArticleRequest
    ): Response<ApiResponse<Any>>
    
    /**
     * Publicar un artículo
     */
    @POST("api/v1/articles/{id}/publish")
    suspend fun publishArticle(@Path("id") articleId: Int): Response<ApiResponse<Any>>
    
    /**
     * Eliminar un artículo
     */
    @HTTP(method = "DELETE", path = "api/v1/articles/{id}")
    suspend fun deleteArticle(@Path("id") articleId: Int): Response<ApiResponse<Any>>
    
    /**
     * Obtener mis artículos
     */
    @POST("api/v1/articles/my-articles")
    suspend fun getMyArticles(
        @Body request: Map<String, Int>
    ): Response<ApiResponse<ArticlesResponse>>
    
    // ==================== PURCHASES ENDPOINTS ====================
    
    /**
     * Crear una compra
     */
    @POST("api/v1/purchases")
    suspend fun createPurchase(@Body request: CreatePurchaseRequest): Response<ApiResponse<PurchaseResponse>>
    
    /**
     * Obtener mis compras
     */
    @GET("api/v1/purchases/my-purchases")
    suspend fun getMyPurchases(): Response<ApiResponse<PurchasesResponse>>
    
    /**
     * Obtener mis ventas
     */
    @GET("api/v1/purchases/my-sales")
    suspend fun getMySales(): Response<ApiResponse<SalesResponse>>
    
    // ==================== COMMENTS ENDPOINTS ====================
    
    /**
     * Crear un comentario
     */
    @POST("api/v1/comments")
    suspend fun createComment(@Body request: CreateCommentRequest): Response<ApiResponse<Map<String, Any>>>
    
    /**
     * Eliminar un comentario
     */
    @HTTP(method = "DELETE", path = "api/v1/comments/{id}")
    suspend fun deleteComment(@Path("id") commentId: Int): Response<ApiResponse<Any>>
    
    // ==================== CATEGORIES ENDPOINTS ====================
    
    /**
     * Obtener todas las categorías
     */
    @GET("api/v1/categories")
    suspend fun getCategories(): Response<ApiResponse<Map<String, List<Category>>>>
}
