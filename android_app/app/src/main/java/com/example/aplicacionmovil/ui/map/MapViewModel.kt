package com.example.aplicacionmovil.ui.map

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.Article
import com.example.aplicacionmovil.domain.models.JsonRpcRequest
import com.example.aplicacionmovil.domain.models.SearchArticlesRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Estados de la pantalla del mapa
 */
sealed class MapState {
    object Loading : MapState()
    data class Success(val articles: List<Article>) : MapState()
    data class Error(val message: String) : MapState()
}

/**
 * ViewModel para la pantalla de mapa
 * Carga artículos con coordenadas para mostrar en el mapa
 */
class MapViewModel(context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)

    private val _mapState = MutableStateFlow<MapState>(MapState.Loading)
    val mapState: StateFlow<MapState> = _mapState.asStateFlow()

    init {
        loadArticlesWithLocation()
    }

    /**
     * Carga todos los artículos que tienen coordenadas de ubicación.
     * Si ninguno tiene coordenadas, usa datos de prueba para la demo/presentación.
     */
    fun loadArticlesWithLocation() {
        viewModelScope.launch {
            _mapState.value = MapState.Loading
            try {
                val response = api.getArticles(
                    JsonRpcRequest(params = SearchArticlesRequest(limit = 100))
                )
                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        // Filtrar solo artículos con coordenadas válidas
                        val articlesWithLocation = apiResponse.data?.articles?.filter { article ->
                            article.latitud != null && article.longitud != null &&
                            article.latitud != 0.0 && article.longitud != 0.0
                        } ?: emptyList()

                        // Si no hay artículos reales con ubicación, usar datos de demo
                        val finalList = if (articlesWithLocation.isEmpty()) {
                            mockArticlesForDemo
                        } else {
                            articlesWithLocation
                        }
                        _mapState.value = MapState.Success(finalList)
                    } else {
                        _mapState.value = MapState.Error(
                            apiResponse?.message ?: "Error al cargar artículos"
                        )
                    }
                } else {
                    // En caso de error HTTP, mostrar los datos de demo
                    _mapState.value = MapState.Success(mockArticlesForDemo)
                }
            } catch (e: Exception) {
                // En caso de error de red, mostrar datos de demo
                _mapState.value = MapState.Success(mockArticlesForDemo)
            }
        }
    }

    fun refresh() {
        loadArticlesWithLocation()
    }

    companion object {
        /**
         * Productos ficticios con coordenadas reales de España para demo/presentación.
         * Se usan automáticamente cuando la API no devuelve artículos con ubicación.
         */
        val mockArticlesForDemo: List<Article> = listOf(
            Article(
                id = 1001,
                codigo = "DEMO-001",
                nombre = "iPhone 14 Pro - Excelente estado",
                descripcion = "iPhone 14 Pro 256GB Space Black, sin arañazos",
                precio = 750f,
                estadoProducto = "como_nuevo",
                localidad = "Madrid",
                latitud = 40.4168,
                longitud = -3.7038
            ),
            Article(
                id = 1002,
                codigo = "DEMO-002",
                nombre = "Bicicleta de montaña Trek",
                descripcion = "Trek Marlin 7, talla M, muy poco uso",
                precio = 420f,
                estadoProducto = "bueno",
                localidad = "Barcelona",
                latitud = 41.3851,
                longitud = 2.1734
            ),
            Article(
                id = 1003,
                codigo = "DEMO-003",
                nombre = "PlayStation 5 + 3 juegos",
                descripcion = "PS5 edición estándar con mando extra y 3 juegos",
                precio = 520f,
                estadoProducto = "como_nuevo",
                localidad = "Valencia",
                latitud = 39.4699,
                longitud = -0.3763
            ),
            Article(
                id = 1004,
                codigo = "DEMO-004",
                nombre = "Sofá esquinero IKEA",
                descripcion = "Sofá KIVIK de 6 plazas, color gris, 2 años de uso",
                precio = 280f,
                estadoProducto = "bueno",
                localidad = "Sevilla",
                latitud = 37.3891,
                longitud = -5.9845
            ),
            Article(
                id = 1005,
                codigo = "DEMO-005",
                nombre = "MacBook Pro M2 13 pulgadas",
                descripcion = "MacBook Pro M2, 8GB RAM, 256GB SSD, como nuevo",
                precio = 1100f,
                estadoProducto = "como_nuevo",
                localidad = "Zaragoza",
                latitud = 41.6488,
                longitud = -0.8891
            ),
            Article(
                id = 1006,
                codigo = "DEMO-006",
                nombre = "Canon EOS 90D + objetivo 50mm",
                descripcion = "Camara reflex con objetivo 50mm f/1.8, maletin incluido",
                precio = 890f,
                estadoProducto = "bueno",
                localidad = "Malaga",
                latitud = 36.7213,
                longitud = -4.4216
            ),
            Article(
                id = 1007,
                codigo = "DEMO-007",
                nombre = "Patinete electrico Xiaomi Pro 2",
                descripcion = "350W, 45km autonomia, poco uso, con cargador",
                precio = 330f,
                estadoProducto = "bueno",
                localidad = "Bilbao",
                latitud = 43.2630,
                longitud = -2.9350
            ),
            Article(
                id = 1008,
                codigo = "DEMO-008",
                nombre = "Mesa de escritorio Gaming",
                descripcion = "Mesa 160x80cm con soporte monitor y gestion de cables",
                precio = 180f,
                estadoProducto = "aceptable",
                localidad = "Alicante",
                latitud = 38.3452,
                longitud = -0.4815
            ),
            Article(
                id = 1009,
                codigo = "DEMO-009",
                nombre = "Samsung Galaxy Tab S8",
                descripcion = "Tablet 11 pulgadas con stylus, 256GB, WiFi + 5G",
                precio = 480f,
                estadoProducto = "como_nuevo",
                localidad = "Valladolid",
                latitud = 41.6523,
                longitud = -4.7245
            ),
            Article(
                id = 1010,
                codigo = "DEMO-010",
                nombre = "Coleccion libros tecnicos programacion",
                descripcion = "15 libros de Java, Python, SQL y Kotlin en perfecto estado",
                precio = 95f,
                estadoProducto = "bueno",
                localidad = "Murcia",
                latitud = 37.9922,
                longitud = -1.1307
            )
        )
    }
}

/**
 * Factory para crear el MapViewModel con contexto
 */
class MapViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(MapViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return MapViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
