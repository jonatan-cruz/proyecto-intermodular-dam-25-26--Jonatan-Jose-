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

    private val _purchasesState = MutableStateFlow<PurchasesState>(PurchasesState.Loading)
    val purchasesState: StateFlow<PurchasesState> = _purchasesState.asStateFlow()

    private val _salesState = MutableStateFlow<SalesState>(SalesState.Loading)
    val salesState: StateFlow<SalesState> = _salesState.asStateFlow()

    init {
        loadProfileData()
    }

    fun loadProfileData() {
        viewModelScope.launch {
            loadUserInfo()
            loadMyArticles()
            loadMyPurchases()
            loadMySales()
        }
    }

    private suspend fun loadUserInfo() {
        try {
            val response = api.getUserProfile()
            if (response.isSuccessful) {
                _userState.value = response.body()?.result?.data
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    fun updateProfile(request: UpdateProfileRequest, onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            try {
                android.util.Log.d("PROFILE_UPDATE", "Enviando actualización de perfil. Avatar len: ${request.avatar?.length ?: 0}")
                val response = api.updateProfile(JsonRpcRequest(params = request))
                if (response.isSuccessful && response.body()?.result?.success == true) {
                    android.util.Log.d("PROFILE_UPDATE", "Actualización exitosa")
                    loadUserInfo() // Recargar datos locales
                    onComplete(true)
                } else {
                    android.util.Log.e("PROFILE_UPDATE", "Error en actualización: ${response.body()?.result?.message}")
                    onComplete(false)
                }
            } catch (e: Exception) {
                android.util.Log.e("PROFILE_UPDATE", "Excepción en actualización", e)
                e.printStackTrace()
                onComplete(false)
            }
        }
    }

    fun changePassword(current: String, new: String, onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            try {
                val params = mapOf("current_password" to current, "new_password" to new)
                val response = api.changePassword(JsonRpcRequest(params = params))
                onComplete(response.isSuccessful && response.body()?.result?.success == true)
            } catch (e: Exception) {
                e.printStackTrace()
                onComplete(false)
            }
        }
    }

    fun deactivateAccount(password: String, onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            try {
                val response = api.deactivateAccount(JsonRpcRequest(params = mapOf("password" to password)))
                onComplete(response.isSuccessful && response.body()?.result?.success == true)
            } catch (e: Exception) {
                e.printStackTrace()
                onComplete(false)
            }
        }
    }

    private suspend fun loadMyArticles() {
        _articlesState.value = ArticlesState.Loading
        try {
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
                _articlesState.value = ArticlesState.Error("Usuario no identificado")
            }
        } catch (e: Exception) {
            _articlesState.value = ArticlesState.Error(e.localizedMessage ?: "Error de conexión")
            e.printStackTrace()
        }
    }

    private suspend fun loadMyPurchases() {
        _purchasesState.value = PurchasesState.Loading
        try {
            val response = api.getMyPurchases()
            if (response.isSuccessful) {
                val apiResponse = response.body()?.result
                if (apiResponse?.success == true) {
                    val purchases = apiResponse.data?.purchases ?: emptyList()
                    _purchasesState.value = PurchasesState.Success(purchases)
                } else {
                    _purchasesState.value = PurchasesState.Error(apiResponse?.message ?: "Error al cargar compras")
                }
            } else {
                _purchasesState.value = PurchasesState.Error("Error ${response.code()}")
            }
        } catch (e: Exception) {
            _purchasesState.value = PurchasesState.Error(e.localizedMessage ?: "Error de conexión")
            e.printStackTrace()
        }
    }

    private suspend fun loadMySales() {
        _salesState.value = SalesState.Loading
        try {
            val response = api.getMySales()
            if (response.isSuccessful) {
                val apiResponse = response.body()?.result
                if (apiResponse?.success == true) {
                    val sales = apiResponse.data?.sales ?: emptyList()
                    _salesState.value = SalesState.Success(sales)
                } else {
                    _salesState.value = SalesState.Error(apiResponse?.message ?: "Error al cargar ventas")
                }
            } else {
                _salesState.value = SalesState.Error("Error ${response.code()}")
            }
        } catch (e: Exception) {
            _salesState.value = SalesState.Error(e.localizedMessage ?: "Error de conexión")
            e.printStackTrace()
        }
    }

    fun confirmSale(saleId: Int) {
        viewModelScope.launch {
            try {
                val response = api.confirmPurchase(saleId)
                if (response.isSuccessful && response.body()?.result?.success == true) {
                    // Refrescar datos tras confirmar
                    loadMySales()
                    loadMyArticles() // El artículo probablemente cambie de estado
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun submitRating(userId: Int, rating: Int, comment: String?, onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            try {
                val request = JsonRpcRequest(params = CreateRatingRequest(userId, rating, comment))
                val response = api.createRating(request)
                if (response.isSuccessful && response.body()?.result?.success == true) {
                    loadUserInfo() // Probablemente se actualice la calificación promedio
                    onComplete(true)
                } else {
                    onComplete(false)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                onComplete(false)
            }
        }
    }
}

sealed class PurchasesState {
    object Loading : PurchasesState()
    data class Success(val purchases: List<Purchase>) : PurchasesState()
    data class Error(val message: String) : PurchasesState()
}

sealed class SalesState {
    object Loading : SalesState()
    data class Success(val sales: List<Sale>) : SalesState()
    data class Error(val message: String) : SalesState()
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
