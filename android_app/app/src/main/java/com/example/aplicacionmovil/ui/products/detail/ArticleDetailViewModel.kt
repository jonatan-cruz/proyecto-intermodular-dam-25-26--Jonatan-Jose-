package com.example.aplicacionmovil.ui.products.detail

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.ApiService
import com.example.aplicacionmovil.domain.models.ArticleDetail
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class ArticleDetailState {
    object Loading : ArticleDetailState()
    data class Success(val article: ArticleDetail) : ArticleDetailState()
    data class Error(val message: String) : ArticleDetailState()
}

class ArticleDetailViewModel(private val api: ApiService) : ViewModel() {

    private val _state = MutableStateFlow<ArticleDetailState>(ArticleDetailState.Loading)
    val state: StateFlow<ArticleDetailState> = _state.asStateFlow()

    fun loadArticleDetail(articleId: Int) {
        viewModelScope.launch {
            _state.value = ArticleDetailState.Loading
            try {
                val response = api.getArticleDetail(articleId)
                if (response.isSuccessful) {
                    val jsonRpcResponse = response.body()
                    val apiResponse = jsonRpcResponse?.result
                    if (apiResponse?.success == true && apiResponse.data != null) {
                        _state.value = ArticleDetailState.Success(apiResponse.data)
                    } else {
                        _state.value = ArticleDetailState.Error(apiResponse?.message ?: "Error desconocido en la API")
                    }
                } else {
                    _state.value = ArticleDetailState.Error("Error en la conexión: ${response.code()}")
                }
            } catch (e: Exception) {
                _state.value = ArticleDetailState.Error("Error: ${e.message}")
            }
        }
    }
}

class ArticleDetailViewModelFactory(private val context: android.content.Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ArticleDetailViewModel::class.java)) {
            val api = com.example.aplicacionmovil.data.remote.api.RetrofitClient.getAuthenticatedService(context)
            @Suppress("UNCHECKED_CAST")
            return ArticleDetailViewModel(api) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
