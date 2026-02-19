package com.example.aplicacionmovil.ui.main

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.CreatePurchaseRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// ==================== VIEWMODEL ====================

class BuyViewModel(context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)

    private val _purchaseState = MutableStateFlow<PurchaseState>(PurchaseState.Idle)
    val purchaseState: StateFlow<PurchaseState> = _purchaseState.asStateFlow()

    /**
     * Llama al endpoint POST /api/v1/purchases para crear la compra.
     * Espeja la lógica del ViewModel de creación de artículo (Vender).
     */
    fun createPurchase(articuloId: Int, precio: Double) {
        if (_purchaseState.value is PurchaseState.Loading) return

        viewModelScope.launch {
            _purchaseState.value = PurchaseState.Loading
            try {
                val request = CreatePurchaseRequest(
                    articuloId = articuloId,
                    precio = precio
                )
                val response = api.createPurchase(request)

                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result

                    if (apiResponse?.success == true) {
                        val purchaseData = apiResponse.data
                        _purchaseState.value = PurchaseState.Success(
                            idCompra = purchaseData?.idCompra ?: "N/A"
                        )
                    } else {
                        _purchaseState.value = PurchaseState.Error(
                            message = apiResponse?.message ?: "Error al procesar la compra"
                        )
                    }
                } else {
                    _purchaseState.value = PurchaseState.Error(
                        message = when (response.code()) {
                            400 -> "El artículo no está disponible para compra"
                            401 -> "Sesión expirada. Por favor, inicia sesión de nuevo"
                            403 -> "No puedes comprar tu propio artículo"
                            404 -> "El artículo no existe"
                            409 -> "El artículo ya fue vendido o reservado"
                            else -> "Error ${response.code()}: ${response.message()}"
                        }
                    )
                }
            } catch (e: Exception) {
                _purchaseState.value = PurchaseState.Error(
                    message = "Error de conexión: ${e.localizedMessage ?: "desconocido"}"
                )
                e.printStackTrace()
            }
        }
    }

    /** Resetear estado para poder reutilizar el botón */
    fun resetState() {
        _purchaseState.value = PurchaseState.Idle
    }
}

// ==================== FACTORY ====================

class BuyViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(BuyViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return BuyViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
