package com.example.aplicacionmovil.ui.profile

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.*
import com.example.aplicacionmovil.ui.main.ArticlesState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ProfileViewModel(context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)

    private val _userState = MutableStateFlow<User?>(null)
    val userState: StateFlow<User?> = _userState.asStateFlow()

    private val _articlesState = MutableStateFlow<ArticlesState>(ArticlesState.Loading)
    val articlesState: StateFlow<ArticlesState> = _articlesState.asStateFlow()

    init {
        loadProfileData()
    }

    fun loadProfileData() {
        viewModelScope.launch {
            loadUserInfo()
            loadMyArticles()
        }
    }

    private suspend fun loadUserInfo() {
        try {
            val response = api.verifyToken(JsonRpcRequest())
            if (response.isSuccessful) {
                _userState.value = response.body()?.result?.data?.get("user")
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private suspend fun loadMyArticles() {
        _articlesState.value = ArticlesState.Loading
        try {
            // Get user ID from current state or session
            val userId = _userState.value?.id
            if (userId != null) {
                val response = api.getMyArticles(JsonRpcRequest(params = mapOf("user_id" to userId)))
                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        val articles = apiResponse.data?.articles ?: emptyList()
                        _articlesState.value = ArticlesState.Success(articles)
                    } else {
                        _articlesState.value = ArticlesState.Error(apiResponse?.message ?: "Error al cargar tus artículos")
                    }
                } else {
                    _articlesState.value = ArticlesState.Error("Error ${response.code()}")
                }
            } else {
                // If user not loaded yet, wait or retry
                _articlesState.value = ArticlesState.Error("Usuario no identificado")
            }
        } catch (e: Exception) {
            _articlesState.value = ArticlesState.Error(e.localizedMessage ?: "Error de conexión")
            e.printStackTrace()
        }
    }
}

class ProfileViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ProfileViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ProfileViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
