package com.example.aplicacionmovil.domain.models

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.repository.ArticleRepository
import com.example.aplicacionmovil.domain.models.Article
import com.example.aplicacionmovil.domain.models.ArticleDetail
import kotlinx.coroutines.launch

/**
 * ViewModel for Articles
 * Manages UI state and business logic
 */
class ArticlesViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = ArticleRepository(application.applicationContext)

    // LiveData for articles list
    private val _articles = MutableLiveData<List<Article>>()
    val articles: LiveData<List<Article>> = _articles

    // LiveData for loading state
    private val _isLoading = MutableLiveData<Boolean>()
    val isLoading: LiveData<Boolean> = _isLoading

    // LiveData for error messages
    private val _error = MutableLiveData<String?>()
    val error: LiveData<String?> = _error

    // LiveData for article detail
    private val _articleDetail = MutableLiveData<ArticleDetail?>()
    val articleDetail: LiveData<ArticleDetail?> = _articleDetail

    /**
     * Load articles with optional filters
     */
    fun loadArticles(
        limit: Int = 20,
        offset: Int = 0,
        categoriaId: Int? = null,
        search: String? = null,
        precioMin: Double? = null,
        precioMax: Double? = null,
        estadoProducto: String? = null,
        localidad: String? = null
    ) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            repository.getArticles(
                limit = limit,
                offset = offset,
                categoriaId = categoriaId,
                search = search,
                precioMin = precioMin,
                precioMax = precioMax,
                estadoProducto = estadoProducto,
                localidad = localidad
            ).onSuccess { articlesResponse ->
                _articles.value = articlesResponse.articles
                _isLoading.value = false
            }.onFailure { exception ->
                _error.value = exception.message ?: "Error al cargar artículos"
                _isLoading.value = false
            }
        }
    }

    /**
     * Load article detail
     */
    fun loadArticleDetail(articleId: Int) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            repository.getArticleDetail(articleId)
                .onSuccess { detail ->
                    _articleDetail.value = detail
                    _isLoading.value = false
                }
                .onFailure { exception ->
                    _error.value = exception.message ?: "Error al cargar detalle"
                    _isLoading.value = false
                }
        }
    }

    /**
     * Load my articles
     */
    fun loadMyArticles(limit: Int = 20, offset: Int = 0) {
        viewModelScope.launch {
            _isLoading.value = true
            _error.value = null

            repository.getMyArticles(limit, offset)
                .onSuccess { articlesResponse ->
                    _articles.value = articlesResponse.articles
                    _isLoading.value = false
                }
                .onFailure { exception ->
                    _error.value = exception.message ?: "Error al cargar mis artículos"
                    _isLoading.value = false
                }
        }
    }

    /**
     * Clear error message
     */
    fun clearError() {
        _error.value = null
    }
}