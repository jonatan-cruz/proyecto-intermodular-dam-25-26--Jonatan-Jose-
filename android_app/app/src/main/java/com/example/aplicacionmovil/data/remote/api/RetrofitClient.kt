/*package com.example.aplicacionmovil.data.remote.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.2:8069/" // Cambiar por la URL real de la API

    // SessionManager para inyectar el token en las peticiones
    var sessionManager: com.example.aplicacionmovil.data.local.SessionManager? = null

    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val httpClient = OkHttpClient.Builder()
        .addInterceptor(logging)
        .addInterceptor { chain ->
            val requestBuilder = chain.request().newBuilder()
            
            // Añadir token si existe
            sessionManager?.fetchAuthToken()?.let { token ->
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }
            
            chain.proceed(requestBuilder.build())
        }
        .build()

    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(httpClient)
            .build()
            .create(ApiService::class.java)
    }
}

 */

package com.example.aplicacionmovil.data.remote.api

import android.content.Context
import android.util.Log
import com.example.aplicacionmovil.data.local.SessionManager
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.2:8069/"

    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    // Cliente sin token (para login y register)
    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(logging)
                    .build()
            )
            .build()
            .create(ApiService::class.java)
    }

    // Cliente con token (para endpoints protegidos)
    fun getAuthenticatedService(context: Context): ApiService {
        val token = SessionManager(context).fetchAuthToken()
        Log.d("AUTH_TOKEN", "Token obtenido: $token") // ← mira Logcat

        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val request = chain.request().newBuilder().apply {
                    if (token != null) {
                        addHeader("Authorization", "Bearer $token")
                    }
                }.build()
                chain.proceed(request)
            }
            .addInterceptor(logging)
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()
            .create(ApiService::class.java)
    }
}
