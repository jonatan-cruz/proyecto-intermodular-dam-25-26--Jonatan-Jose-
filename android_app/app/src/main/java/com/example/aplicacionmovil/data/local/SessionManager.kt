package com.example.aplicacionmovil.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.core.content.edit
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SessionManager(context: Context) {
    
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    companion object {
        private const val USER_TOKEN = "user_token"
        private const val USER_ID    = "user_id"
    }

    /**
     * Guarda el token del usuario de forma encriptada
     */
    fun saveAuthToken(token: String) {
        prefs.edit {
            putString(USER_TOKEN, token)
        }
    }

    /**
     * Recupera el token del usuario
     */
    fun fetchAuthToken(): String? {
        return prefs.getString(USER_TOKEN, null)
    }

    /**
     * Guarda el ID numérico del usuario autenticado
     */
    fun saveUserId(id: Int) {
        prefs.edit { putInt(USER_ID, id) }
    }

    /**
     * Recupera el ID del usuario autenticado (-1 si no existe)
     */
    fun getUserId(): Int {
        return prefs.getInt(USER_ID, -1)
    }

    /**
     * Elimina el token y el ID de usuario (Logout)
     */
    fun clearSession() {
        prefs.edit {
            remove(USER_TOKEN)
            remove(USER_ID)
        }
    }
}
