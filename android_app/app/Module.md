# Module Second Market App

Aplicación Android de marketplace de segunda mano.

## Paquetes

### com.example.aplicacionmovil.data
Capa de datos que gestiona el acceso a datos locales y remotos.

- **local**: Gestión de sesión con `SessionManager` usando EncryptedSharedPreferences
- **remote.api**: Cliente Retrofit y definición de endpoints `ApiService`
- **repository**: Repositorios para acceso a datos

### com.example.aplicacionmovil.domain.models
Modelos de dominio de la aplicación.

- **Article**: Modelo de artículo/producto
- **User**: Modelo de usuario
- **ChatConversation**: Modelo de conversación de chat
- **ChatMessage**: Modelo de mensaje
- **Requests**: Data classes para peticiones a la API
- **Response**: Data classes para respuestas de la API

### com.example.aplicacionmovil.ui
Capa de presentación con Jetpack Compose.

- **main**: Pantallas principales (Home, Login, Register, Search)
- **chat**: Sistema de mensajería (ChatListScreen, ChatDetailScreen)
- **map**: Mapa de productos con Google Maps
- **products**: Creación y detalle de artículos
- **profile**: Perfil de usuario
- **settings**: Configuración de la app
- **navigation**: Componentes de navegación (BottomNavBar)
- **theme**: Tema Material 3 (colores, tipografía)

## Arquitectura

La aplicación sigue el patrón **MVVM**:

```
View (Composables) <-> ViewModel <-> Repository <-> API/Local
```

Cada pantalla tiene su propio ViewModel que expone estados mediante `StateFlow`.
