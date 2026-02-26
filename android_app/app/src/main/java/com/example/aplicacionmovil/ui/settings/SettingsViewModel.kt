package com.example.aplicacionmovil.ui.settings

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.local.SessionManager
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.google.gson.JsonObject
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import com.example.aplicacionmovil.domain.models.UpdateProfileRequest
import com.example.aplicacionmovil.domain.models.User
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class SettingsViewModel(context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)
    private val sessionManager = SessionManager(context)

    private val _userState = MutableStateFlow<User?>(null)
    val userState: StateFlow<User?> = _userState.asStateFlow()

    private val _logoutEvents = MutableSharedFlow<Unit>()
    val logoutEvents: SharedFlow<Unit> = _logoutEvents.asSharedFlow()

    init {
        loadUserInfo()
    }

    fun loadUserInfo() {
        viewModelScope.launch {
            try {
                val response = api.getUserProfile()
                if (response.isSuccessful) {
                    _userState.value = response.body()?.result?.data
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            try {
                // Notificar al servidor (opcional, pero buena práctica)
                api.logout(JsonObject())
            } catch (e: Exception) {
                e.printStackTrace()
            } finally {
                // Limpiar sesión localmente pase lo que pase
                sessionManager.clearSession()
                _logoutEvents.emit(Unit)
            }
        }
    }

    fun updateProfile(request: UpdateProfileRequest, onComplete: (Boolean) -> Unit) {
        viewModelScope.launch {
            try {
                android.util.Log.d("SETTINGS_UPDATE", "Enviando actualización de perfil desde Settings. Avatar len: ${request.avatar?.length ?: 0}")
                val response = api.updateProfile(JsonRpcRequest(params = request))
                
                if (response.isSuccessful && response.body()?.result?.success == true) {
                    android.util.Log.d("SETTINGS_UPDATE", "Actualización desde Settings exitosa")
                    loadUserInfo()
                    onComplete(true)
                } else {
                    android.util.Log.e("SETTINGS_UPDATE", "Error en actualización desde Settings: ${response.body()?.result?.message}")
                    onComplete(false)
                }
            } catch (e: Exception) {
                android.util.Log.e("SETTINGS_UPDATE", "Excepción en actualización desde Settings", e)
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
}

class SettingsViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SettingsViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return SettingsViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
