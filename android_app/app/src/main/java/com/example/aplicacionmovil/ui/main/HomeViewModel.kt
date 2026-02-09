package com.example.aplicacionmovil.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.SearchArticlesRequest
import com.example.aplicacionmovil.domain.models.Article
import com.example.aplicacionmovil.domain.models.User
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * ViewModel simplificado que obtiene ApiService directamente de RetrofitClient
 * Esta versión NO requiere factory y se puede usar con viewModel() directamente
 */
class HomeViewModel : ViewModel() {

    // Obtener ApiService del singleton RetrofitClient
    private val apiService = RetrofitClient.apiService

    private val _articlesState = MutableStateFlow<ArticlesState>(ArticlesState.Idle)
    val articlesState: StateFlow<ArticlesState> = _articlesState.asStateFlow()

    private val _userState = MutableStateFlow<User?>(null)
    val userState: StateFlow<User?> = _userState.asStateFlow()

    init {
        loadArticles()
        loadUserInfo()
    }

    fun loadArticles() {
        viewModelScope.launch {
            _articlesState.value = ArticlesState.Loading
            try {
                val request = SearchArticlesRequest(
                    limit = 50,
                    offset = 0,
                    categoriaId = null,
                    search = null,
                    precioMin = null,
                    precioMax = null,
                    estadoProducto = null,
                    localidad = null
                )

                val response = apiService.getArticles(request)

                if (response.isSuccessful && response.body() != null) {
                    val apiResponse = response.body()!!

                    // La respuesta es ApiResponse<ArticlesResponse> directamente
                    // Acceder a los artículos según tu estructura
                    val articlesData = apiResponse.data
                    val articles = articlesData?.articles ?: emptyList()

                    _articlesState.value = ArticlesState.Success(articles)
                } else {
                    _articlesState.value = ArticlesState.Error("Error al cargar los artículos")
                }
            } catch (e: Exception) {
                _articlesState.value = ArticlesState.Error(
                    e.localizedMessage ?: "Error desconocido"
                )
            }
        }
    }

    fun searchArticles(
        query: String,
        categoryId: Int? = null,
        priceRange: ClosedFloatingPointRange<Float> = 0f..10000f
    ) {
        viewModelScope.launch {
            _articlesState.value = ArticlesState.Loading
            try {
                val request = SearchArticlesRequest(
                    limit = 50,
                    offset = 0,
                    categoriaId = categoryId,
                    search = query.ifEmpty { null },
                    precioMin = if (priceRange.start > 0f) priceRange.start.toDouble() else null,
                    precioMax = if (priceRange.endInclusive < 10000f) priceRange.endInclusive.toDouble() else null,
                    estadoProducto = null,
                    localidad = null
                )

                val response = apiService.getArticles(request)

                if (response.isSuccessful && response.body() != null) {
                    val apiResponse = response.body()!!
                    val articlesData = apiResponse.data
                    val articles = articlesData?.articles ?: emptyList()

                    _articlesState.value = ArticlesState.Success(articles)
                } else {
                    _articlesState.value = ArticlesState.Error("Error en la búsqueda")
                }
            } catch (e: Exception) {
                _articlesState.value = ArticlesState.Error(
                    e.localizedMessage ?: "Error en la búsqueda"
                )
            }
        }
    }

    private fun loadUserInfo() {
        viewModelScope.launch {
            try {
                val response = apiService.verifyToken()

                if (response.isSuccessful && response.body() != null) {
                    val jsonRpcResponse = response.body()!!
                    val apiResponse = jsonRpcResponse.result

                    // Acceder al usuario según tu estructura
                    val userMap = apiResponse.data
                    val userData = userMap?.get("user")

                    userData?.let {
                        _userState.value = it
                    }
                }
            } catch (e: Exception) {
                // Error al cargar info del usuario
                e.printStackTrace()
            }
        }
    }

    fun resetState() {
        _articlesState.value = ArticlesState.Idle
    }
}

// Estados del ViewModel
sealed class ArticlesState {
    object Idle : ArticlesState()
    object Loading : ArticlesState()
    data class Success(val articles: List<Article>) : ArticlesState()
    data class Error(val message: String) : ArticlesState()
}