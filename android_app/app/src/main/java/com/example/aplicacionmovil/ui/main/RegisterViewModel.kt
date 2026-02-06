package com.example.aplicacionmovil.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.RegisterRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

sealed class RegisterState {
    object Idle : RegisterState()
    object Loading : RegisterState()
    data class Success(val message: String) : RegisterState()
    data class Error(val message: String) : RegisterState()
}

class RegisterViewModel : ViewModel() {
    private val _registerState = MutableStateFlow<RegisterState>(RegisterState.Idle)
    val registerState: StateFlow<RegisterState> = _registerState

    fun register(
        name: String,
        login: String,
        password: String,
        telefono: String? = null,
        ubicacion: String? = null,
        biografia: String? = null
    ) {
        viewModelScope.launch {
            _registerState.value = RegisterState.Loading
            try {
                val response = RetrofitClient.apiService.register(
                    RegisterRequest(
                        name = name,
                        login = login,
                        password = password,
                        telefono = telefono,
                        ubicacion = ubicacion,
                        biografia = biografia
                    )
                )

                if (response.isSuccessful) {
                    val rpcBody = response.body()
                    val apiBody = rpcBody?.result
                    if (apiBody?.success == true) {
                        _registerState.value = RegisterState.Success(
                            apiBody.message ?: "Usuario registrado exitosamente"
                        )
                    } else {
                        _registerState.value = RegisterState.Error(
                            apiBody?.message ?: "Error en la lógica del servidor"
                        )
                    }
                } else {
                    val errorMsg = response.errorBody()?.string() ?: "Error HTTP ${response.code()}"
                    _registerState.value = RegisterState.Error(
                        "Error del servidor (${response.code()}): $errorMsg"
                    )
                }
            } catch (e: Exception) {
                _registerState.value = RegisterState.Error("Error de conexión: ${e.message}")
            }
        }
    }

    fun resetState() {
        _registerState.value = RegisterState.Idle
    }
}