/*package com.example.aplicacionmovil.data.remote.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.27:8069/" // Cambiar por la URL real de la API

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
import java.util.concurrent.TimeUnit

object RetrofitClient {
    private const val BASE_URL = "http://10.0.2.2:8069/"

    // Log con BODY solo para el cliente público (respuestas pequeñas: login, register)
    private val loggingBody = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    // Log con HEADERS para el cliente autenticado — evita leer el body de 426KB
    // que con Connection: close provocaba ProtocolException: unexpected end of stream
    private val loggingHeaders = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.HEADERS
    }

    // Cliente sin token (para login y register — respuestas pequeñas)
    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(loggingBody)
                    .build()
            )
            .build()
            .create(ApiService::class.java)
    }

    // Cliente con token (para endpoints protegidos — puede recibir respuestas grandes)
    fun getAuthenticatedService(context: Context): ApiService {
        val sessionManager = SessionManager(context)

        val client = OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)   // 60s para respuestas grandes con imágenes
            .retryOnConnectionFailure(true)
            .addInterceptor { chain ->
                val token = sessionManager.fetchAuthToken()
                Log.d("AUTH_TOKEN", "Token usado: $token")
                val requestBuilder = chain.request().newBuilder()
                if (token != null) {
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
                chain.proceed(requestBuilder.build())
            }
            .addInterceptor(loggingHeaders)      // solo headers, no consume el body
            .build()

        return Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()
            .create(ApiService::class.java)
    }
}
