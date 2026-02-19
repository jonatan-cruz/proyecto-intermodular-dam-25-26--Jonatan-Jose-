package com.example.aplicacionmovil.data.repository

import android.content.Context
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.*

/**
 * Repository for Article operations
 * Handles API calls with proper authentication
 */
class ArticleRepository(private val context: Context) {

    /**
     * Get list of articles with search filters
     */
    suspend fun getArticles(
        limit: Int = 20,
        offset: Int = 0,
        categoriaId: Int? = null,
        search: String? = null,
        precioMin: Double? = null,
        precioMax: Double? = null,
        estadoProducto: String? = null,
        localidad: String? = null
    ): Result<ArticlesResponse> {
        return try {
            val request = SearchArticlesRequest(
                limit = limit,
                offset = offset,
                categoriaId = categoriaId,
                search = search,
                precioMin = precioMin,
                precioMax = precioMax,
                estadoProducto = estadoProducto,
                localidad = localidad
            )

            // Use authenticated service
            val response = RetrofitClient.getAuthenticatedService(context)
                .getArticles(request)

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success && apiResponse.data != null) {
                    Result.success(apiResponse.data)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()} - ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Get article detail by ID
     */
    suspend fun getArticleDetail(articleId: Int): Result<ArticleDetail> {
        return try {
            val response = RetrofitClient.getAuthenticatedService(context)
                .getArticleDetail(articleId, com.google.gson.JsonObject())

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success && apiResponse.data != null) {
                    Result.success(apiResponse.data)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Get my articles
     */
    suspend fun getMyArticles(limit: Int = 20, offset: Int = 0): Result<ArticlesResponse> {
        return try {
            val request = mapOf("limit" to limit, "offset" to offset)

            val response = RetrofitClient.getAuthenticatedService(context)
                .getMyArticles(request)

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success && apiResponse.data != null) {
                    Result.success(apiResponse.data)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Create a new article
     */
    suspend fun createArticle(request: CreateArticleRequest): Result<Map<String, Any>> {
        return try {
            val response = RetrofitClient.getAuthenticatedService(context)
                .createArticle(request)

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success && apiResponse.data != null) {
                    Result.success(apiResponse.data)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Update an existing article
     */
    suspend fun updateArticle(articleId: Int, request: UpdateArticleRequest): Result<Any> {
        return try {
            val response = RetrofitClient.getAuthenticatedService(context)
                .updateArticle(articleId, request)

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Publish an article
     */
    suspend fun publishArticle(articleId: Int): Result<Any> {
        return try {
            val response = RetrofitClient.getAuthenticatedService(context)
                .publishArticle(articleId, com.google.gson.JsonObject())

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Delete an article
     */
    suspend fun deleteArticle(articleId: Int): Result<Any> {
        return try {
            val response = RetrofitClient.getAuthenticatedService(context)
                .deleteArticle(articleId)

            if (response.isSuccessful && response.body() != null) {
                val jsonRpcResponse = response.body()!!
                val apiResponse = jsonRpcResponse.result

                if (apiResponse.success) {
                    Result.success(Unit)
                } else {
                    Result.failure(Exception(apiResponse.message ?: "Error desconocido"))
                }
            } else {
                Result.failure(Exception("Error HTTP: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}