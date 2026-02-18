package com.example.aplicacionmovil.ui.products.create

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.CreateArticleRequest
import com.example.aplicacionmovil.domain.models.ImageRequest
import com.example.aplicacionmovil.utils.ImageUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class CreateArticleViewModel : ViewModel() {

    private val apiService = RetrofitClient.apiService

    private val _uiState = MutableStateFlow<CreateArticleUiState>(CreateArticleUiState.Idle)
    val uiState: StateFlow<CreateArticleUiState> = _uiState.asStateFlow()

    // Form states
    var name = MutableStateFlow("")
    var description = MutableStateFlow("")
    var price = MutableStateFlow("")
    var categoryId = MutableStateFlow<Int?>(null)
    var selectedImages = MutableStateFlow<List<Uri>>(emptyList())
    
    // Categories from API
    private val _categories = MutableStateFlow<List<com.example.aplicacionmovil.domain.models.Category>>(emptyList())
    val categories: StateFlow<List<com.example.aplicacionmovil.domain.models.Category>> = _categories.asStateFlow()

    fun loadCategories(context: Context) {
        // Asegurar que RetrofitClient tiene el SessionManager
        if (RetrofitClient.sessionManager == null) {
             RetrofitClient.sessionManager = com.example.aplicacionmovil.data.local.SessionManager(context)
        }

        viewModelScope.launch {
            try {
                val response = apiService.getCategories(emptyMap())
                if (response.isSuccessful) {
                    val jsonRpcResponse = response.body()
                    val apiResponse = jsonRpcResponse?.result
                    
                    if (apiResponse?.success == true) {
                        val categoriesMap = apiResponse.data
                        val allCategories = categoriesMap?.get("categories") 
                        
                        if (allCategories != null) {
                            _categories.value = allCategories
                        } else {
                            // Si no viene en el mapa "categories", intentar ver si rpcResult.data es la lista directamente
                            _uiState.value = CreateArticleUiState.Error("Estructura de categorías inesperada")
                        }
                    } else {
                        _uiState.value = CreateArticleUiState.Error("Error del servidor: ${apiResponse?.message ?: "Sin mensaje"}")
                    }
                } else {
                    _uiState.value = CreateArticleUiState.Error("Error HTTP ${response.code()}: ${response.message()}")
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.value = CreateArticleUiState.Error("Error de red: ${e.localizedMessage}")
            }
        }
    }

    fun onImagesSelected(uris: List<Uri>) {
        val current = selectedImages.value.toMutableList()
        current.addAll(uris)
        selectedImages.value = current
    }

    fun removeImage(uri: Uri) {
        val current = selectedImages.value.toMutableList()
        current.remove(uri)
        selectedImages.value = current
    }

    fun createArticle(context: Context, onSuccess: () -> Unit) {
        if (!validateForm()) return

        // Asegurar que RetrofitClient tiene el SessionManager
        if (RetrofitClient.sessionManager == null) {
            RetrofitClient.sessionManager = com.example.aplicacionmovil.data.local.SessionManager(context)
        }

        viewModelScope.launch {
            _uiState.value = CreateArticleUiState.Loading
            try {
                // Convertir imágenes a Base64
                val imageRequests = selectedImages.value.mapIndexed { index, uri ->
                    val base64 = ImageUtils.uriToBase64(context, uri) ?: ""
                    ImageRequest(
                        image = base64,
                        name = "image_$index.jpg",
                        sequence = index
                    )
                }.filter { it.image.isNotEmpty() }

                val request = CreateArticleRequest(
                    nombre = name.value,
                    descripcion = description.value,
                    precio = price.value.toDoubleOrNull() ?: 0.0,
                    estadoProducto = "nuevo", // Valor por defecto conveniente
                    categoriaId = categoryId.value ?: 1,
                    imagenes = imageRequests
                )

                val response = apiService.createArticle(request)

                if (response.isSuccessful) {
                    val rpcResult = response.body()?.result
                    if (rpcResult?.success == true) {
                        _uiState.value = CreateArticleUiState.Success
                        onSuccess()
                    } else {
                        _uiState.value = CreateArticleUiState.Error("Error: ${rpcResult?.message ?: "Desconocido"}")
                    }
                } else {
                    _uiState.value = CreateArticleUiState.Error("Error HTTP ${response.code()}: ${response.message()}")
                }
            } catch (e: Exception) {
                _uiState.value = CreateArticleUiState.Error("Error: ${e.localizedMessage}")
            }
        }
    }

    private fun validateForm(): Boolean {
        if (name.value.isBlank()) {
            _uiState.value = CreateArticleUiState.Error("El nombre es obligatorio")
            return false
        }
        if (price.value.toDoubleOrNull() == null) {
            _uiState.value = CreateArticleUiState.Error("El precio debe ser un número válido")
            return false
        }
        if (categoryId.value == null) {
            _uiState.value = CreateArticleUiState.Error("Selecciona una categoría")
            return false
        }
        return true
    }
}

sealed class CreateArticleUiState {
    object Idle : CreateArticleUiState()
    object Loading : CreateArticleUiState()
    object Success : CreateArticleUiState()
    data class Error(val message: String) : CreateArticleUiState()
}
