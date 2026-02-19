package com.example.aplicacionmovil.ui.products.create

import android.content.Context
import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.Category
import com.example.aplicacionmovil.domain.models.CreateArticleRequest
import com.example.aplicacionmovil.domain.models.ImageRequest
import com.example.aplicacionmovil.utils.ImageUtils
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// ==================== ESTADOS ====================

sealed class CategoriesFormState {
    object Loading : CategoriesFormState()
    data class Success(val categories: List<Category>) : CategoriesFormState()
    data class Error(val message: String) : CategoriesFormState()
}

// ==================== VIEWMODEL ====================

class CreateArticleViewModel(context: Context) : ViewModel() {

    // Igual que HomeViewModel: servicio autenticado inicializado con contexto
    private val api = RetrofitClient.getAuthenticatedService(context)

    // Form states
    var name = MutableStateFlow("")
    var description = MutableStateFlow("")
    var price = MutableStateFlow("")
    var categoryId = MutableStateFlow<Int?>(null)
    var selectedImages = MutableStateFlow<List<Uri>>(emptyList())

    // Estado de categorías (igual que CategoriesState en HomeViewModel)
    private val _categoriesState = MutableStateFlow<CategoriesFormState>(CategoriesFormState.Loading)
    val categoriesState: StateFlow<CategoriesFormState> = _categoriesState.asStateFlow()

    // Estado general del formulario
    private val _uiState = MutableStateFlow<CreateArticleUiState>(CreateArticleUiState.Idle)
    val uiState: StateFlow<CreateArticleUiState> = _uiState.asStateFlow()

    init {
        loadCategories()
    }

    // ==================== CATEGORÍAS ====================
    // Mismo patrón que HomeViewModel.loadCategories()

    fun loadCategories() {
        viewModelScope.launch {
            _categoriesState.value = CategoriesFormState.Loading
            try {
                val response = api.getCategories(JsonRpcRequest())
                if (response.isSuccessful) {
                    val result = response.body()?.result
                    if (result?.success == true) {
                        val categories: List<Category> =
                            result.data?.get("categories") ?: emptyList()
                        _categoriesState.value = CategoriesFormState.Success(categories)
                    } else {
                        _categoriesState.value = CategoriesFormState.Error(
                            result?.message ?: "Error al cargar categorías"
                        )
                    }
                } else {
                    _categoriesState.value = CategoriesFormState.Error(
                        "Error ${response.code()}: ${response.message()}"
                    )
                }
            } catch (e: Exception) {
                _categoriesState.value = CategoriesFormState.Error(
                    "[${e.javaClass.simpleName}] ${e.localizedMessage ?: "sin mensaje"}"
                )
                e.printStackTrace()
            }
        }
    }

    // ==================== IMÁGENES ====================

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

    // ==================== CREAR ARTÍCULO ====================

    fun createArticle(context: Context, onSuccess: () -> Unit) {
        if (!validateForm()) return

        viewModelScope.launch {
            _uiState.value = CreateArticleUiState.Loading
            try {
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
                    estadoProducto = "nuevo",
                    categoriaId = categoryId.value ?: 1,
                    imagenes = imageRequests
                )

                val response = api.createArticle(JsonRpcRequest(params = request))

                if (response.isSuccessful) {
                    val rpcResult = response.body()?.result
                    if (rpcResult?.success == true) {
                        _uiState.value = CreateArticleUiState.Success
                        onSuccess()
                    } else {
                        _uiState.value = CreateArticleUiState.Error(
                            "Error: ${rpcResult?.message ?: "Desconocido"}"
                        )
                    }
                } else {
                    _uiState.value = CreateArticleUiState.Error(
                        "Error HTTP ${response.code()}: ${response.message()}"
                    )
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

// ==================== FACTORY ====================

class CreateArticleViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        @Suppress("UNCHECKED_CAST")
        return CreateArticleViewModel(context) as T
    }
}

// ==================== ESTADOS UI ====================

sealed class CreateArticleUiState {
    object Idle : CreateArticleUiState()
    object Loading : CreateArticleUiState()
    object Success : CreateArticleUiState()
    data class Error(val message: String) : CreateArticleUiState()
}
