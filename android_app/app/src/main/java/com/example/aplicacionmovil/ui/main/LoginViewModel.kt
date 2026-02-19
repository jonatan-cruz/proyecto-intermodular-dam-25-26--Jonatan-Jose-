package com.example.aplicacionmovil.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import com.example.aplicacionmovil.domain.models.LoginRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

sealed class LoginState {
    object Idle : LoginState()
    object Loading : LoginState()
    data class Success(val message: String) : LoginState()
    data class Error(val message: String) : LoginState()
}

class LoginViewModel : ViewModel() {
    private val _loginState = MutableStateFlow<LoginState>(LoginState.Idle)
    val loginState: StateFlow<LoginState> = _loginState

    fun login(email: String, password: String, sessionManager: com.example.aplicacionmovil.data.local.SessionManager) {
        viewModelScope.launch {
            _loginState.value = LoginState.Loading
            try {
                val response = RetrofitClient.apiService.login(JsonRpcRequest(params = LoginRequest(email, password)))
                if (response.isSuccessful) {
                    val rpcBody = response.body()
                    val apiBody = rpcBody?.result
                    if (apiBody?.success == true) {
                        // Guardar el token si viene en la respuesta
                        apiBody.data?.token?.let { token ->
                            sessionManager.saveAuthToken(token)
                        }
                        _loginState.value = LoginState.Success("Login exitoso")
                    } else {
                        _loginState.value = LoginState.Error(apiBody?.message ?: "Error en la lógica del servidor")
                    }
                } else {
                    val errorMsg = response.errorBody()?.string() ?: "Error HTTP ${response.code()}"
                    _loginState.value = LoginState.Error("Error del servidor (${response.code()}): $errorMsg")
                }
            } catch (e: Exception) {
                _loginState.value = LoginState.Error("Error de conexión: ${e.message}")
            }
        }
    }
    
    fun resetState() {
        _loginState.value = LoginState.Idle
    }
}
