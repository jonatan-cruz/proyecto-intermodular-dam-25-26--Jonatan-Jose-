package com.example.aplicacionmovil.data.remote

import android.content.Context
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(private val context: Context) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = getToken(context) // Lee el token guardado

        val request = if (token != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }

        return chain.proceed(request)
    }

    private fun getToken(context: Context): String? {
        val prefs = context.getSharedPreferences("auth_prefs", Context.MODE_PRIVATE)
        return prefs.getString("jwt_token", null)
    }
}