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
import kotlinx.coroutines.launch

class SettingsViewModel(context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)
    private val sessionManager = SessionManager(context)

    private val _logoutEvents = MutableSharedFlow<Unit>()
    val logoutEvents: SharedFlow<Unit> = _logoutEvents.asSharedFlow()

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
