package com.example.aplicacionmovil.ui.main

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.*
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// ==================== ESTADOS ====================

sealed class ArticlesState {
    object Loading : ArticlesState()
    data class Success(val articles: List<Article>) : ArticlesState()
    data class Error(val message: String) : ArticlesState()
}

sealed class CategoriesState {
    object Loading : CategoriesState()
    data class Success(val categories: List<Category>) : CategoriesState()
    data class Error(val message: String) : CategoriesState()
}

// ==================== VIEWMODEL ====================

class HomeViewModel(context: Context) : ViewModel() {

    // Usa RetrofitClient.getAuthenticatedService para inyectar el token automáticamente
    private val api = RetrofitClient.getAuthenticatedService(context)

    private val _articlesState = MutableStateFlow<ArticlesState>(ArticlesState.Loading)
    val articlesState: StateFlow<ArticlesState> = _articlesState.asStateFlow()

    private val _categoriesState = MutableStateFlow<CategoriesState>(CategoriesState.Loading)
    val categoriesState: StateFlow<CategoriesState> = _categoriesState.asStateFlow()

    private val _userState = MutableStateFlow<User?>(null)
    val userState: StateFlow<User?> = _userState.asStateFlow()

    init {
        loadUserInfo()
        loadCategories()
        loadArticles()
    }

    // ==================== USUARIO ====================
    // Respuesta: JsonRpcResponse<ApiResponse<Map<String, User>>>
    // Token verificado -> result.data["user"]

    private fun loadUserInfo() {
        viewModelScope.launch {
            try {
                val response = api.verifyToken(JsonRpcRequest())
                if (response.isSuccessful) {
                    _userState.value = response.body()?.result?.data?.get("user")
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    // ==================== CATEGORÍAS ====================
    // Respuesta: JsonRpcResponse<ApiResponse<Map<String, List<Category>>>>
    // Categorías -> result.data["categories"]

    fun loadCategories() {
        viewModelScope.launch {
            _categoriesState.value = CategoriesState.Loading
            try {
                val response = api.getCategories(JsonRpcRequest())
                if (response.isSuccessful) {
                    val result = response.body()?.result
                    if (result?.success == true) {
                        val categories: List<Category> =
                            result.data?.get("categories") ?: emptyList()
                        _categoriesState.value = CategoriesState.Success(categories)
                    } else {
                        _categoriesState.value = CategoriesState.Error(
                            result?.message ?: "Error al cargar categorías"
                        )
                    }
                } else {
                    _categoriesState.value = CategoriesState.Error(
                        "Error ${response.code()}: ${response.message()}"
                    )
                }
            } catch (e: Exception) {
                _categoriesState.value = CategoriesState.Error(
                    "[${e.javaClass.simpleName}] ${e.localizedMessage ?: "sin mensaje"}"
                )
                e.printStackTrace()
            }
        }
    }

    // ==================== ARTÍCULOS ====================
    // Respuesta: JsonRpcResponse<ApiResponse<ArticlesResponse>>
    // Artículos -> result.data.articles

    fun loadArticles() {
        viewModelScope.launch {
            _articlesState.value = ArticlesState.Loading
            try {
                val response = api.getArticles(JsonRpcRequest(params = SearchArticlesRequest()))
                android.util.Log.d("HOME_ARTICLES", "HTTP code: ${response.code()}, isSuccessful: ${response.isSuccessful}")
                if (response.isSuccessful) {
                    val jsonRpcResponse = response.body()
                    android.util.Log.d("HOME_ARTICLES", "body null? ${jsonRpcResponse == null}")
                    android.util.Log.d("HOME_ARTICLES", "result null? ${jsonRpcResponse?.result == null}")
                    val apiResponse = jsonRpcResponse?.result
                    android.util.Log.d("HOME_ARTICLES", "success? ${apiResponse?.success}, data null? ${apiResponse?.data == null}")

                    if (apiResponse?.success == true) {
                        val articles: List<Article> = apiResponse.data?.articles ?: emptyList()
                        android.util.Log.d("HOME_ARTICLES", "Articles loaded: ${articles.size}")
                        _articlesState.value = ArticlesState.Success(articles)
                    } else {
                        val errMsg = apiResponse?.message ?: "Error al cargar artículos (success=false o body nulo)"
                        android.util.Log.e("HOME_ARTICLES", "API error: $errMsg")
                        _articlesState.value = ArticlesState.Error(errMsg)
                    }
                } else {
                    val errMsg = "Error HTTP ${response.code()}: ${response.message()}"
                    android.util.Log.e("HOME_ARTICLES", errMsg)
                    _articlesState.value = ArticlesState.Error(errMsg)
                }
            } catch (e: Exception) {
                android.util.Log.e("HOME_ARTICLES", "Exception: ${e.javaClass.simpleName} - ${e.localizedMessage}", e)
                _articlesState.value = ArticlesState.Error(
                    "Error de conexión: ${e.localizedMessage ?: "desconocido"}"
                )
                e.printStackTrace()
            }
        }
    }

    fun searchArticles(
        query: String = "",
        categoryId: Int? = null,
        priceRange: ClosedFloatingPointRange<Float>? = null
    ) {
        viewModelScope.launch {
            _articlesState.value = ArticlesState.Loading
            try {
                val request = SearchArticlesRequest(
                    search = query.ifEmpty { null },
                    categoriaId = categoryId,
                    precioMin = priceRange?.start?.toDouble(),
                    precioMax = priceRange?.endInclusive?.toDouble()
                )
                val response = api.getArticles(JsonRpcRequest(params = request))
                if (response.isSuccessful) {
                    // FIXED: Unwrap JsonRpcResponse first, then ApiResponse
                    val jsonRpcResponse = response.body()
                    val apiResponse = jsonRpcResponse?.result

                    if (apiResponse?.success == true) {
                        val articles: List<Article> = apiResponse.data?.articles ?: emptyList()
                        _articlesState.value = ArticlesState.Success(articles)
                    } else {
                        _articlesState.value = ArticlesState.Error(
                            apiResponse?.message ?: "Sin resultados"
                        )
                    }
                } else {
                    _articlesState.value = ArticlesState.Error(
                        "Error ${response.code()}: ${response.message()}"
                    )
                }
            } catch (e: Exception) {
                _articlesState.value = ArticlesState.Error(
                    "Error de conexión: ${e.localizedMessage ?: "desconocido"}"
                )
                e.printStackTrace()
            }
        }
    }

    fun refresh() {
        loadUserInfo()
        loadCategories()
        loadArticles()
    }
}