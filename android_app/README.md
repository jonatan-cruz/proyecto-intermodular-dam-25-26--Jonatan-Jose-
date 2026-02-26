# Second Market - Aplicación Android

Aplicación móvil de marketplace de segunda mano desarrollada con Jetpack Compose y Kotlin.

## Descripción

Second Market es una aplicación de compraventa de artículos de segunda mano que permite a los usuarios:
- Publicar artículos con fotos, descripción y ubicación
- Buscar y filtrar productos por categoría, precio y ubicación
- Contactar con vendedores mediante chat en tiempo real
- Realizar compras y gestionar ventas
- Ver productos en un mapa interactivo

## Tecnologías

| Tecnología | Uso |
|------------|-----|
| **Kotlin** | Lenguaje principal |
| **Jetpack Compose** | UI declarativa |
| **Material Design 3** | Sistema de diseño |
| **Retrofit** | Cliente HTTP/API |
| **Coroutines + Flow** | Programación asíncrona |
| **Navigation Compose** | Navegación entre pantallas |
| **Google Maps Compose** | Integración de mapas |
| **Coil** | Carga de imágenes |
| **EncryptedSharedPreferences** | Almacenamiento seguro de sesión |
| **Dokka** | Generación de documentación |

## Arquitectura

La aplicación sigue el patrón **MVVM (Model-View-ViewModel)**:

```
app/
├── data/
│   ├── local/          # SessionManager (almacenamiento local)
│   ├── remote/api/     # ApiService, RetrofitClient
│   └── repository/     # Repositorios
├── domain/models/      # Modelos de datos, Requests, Responses
├── ui/
│   ├── chat/           # Pantallas de chat
│   ├── main/           # Home, Login, Register, Search
│   ├── map/            # Mapa de productos
│   ├── navigation/     # BottomNavBar
│   ├── products/       # Crear, detalle de artículos
│   ├── profile/        # Perfil de usuario
│   ├── settings/       # Configuración
│   └── theme/          # Colores, tipografía, tema
└── utils/              # Utilidades (ImageUtils)
```

## Requisitos

- Android Studio Hedgehog (2023.1.1) o superior
- Android SDK 24+ (minSdk)
- Android SDK 36 (targetSdk/compileSdk)
- JDK 11
- Google Maps API Key (para funcionalidad de mapas)

## Configuración

### 1. Clonar el repositorio
```bash
git clone https://github.com/jonatan-cruz/proyecto-intermodular-dam-25-26--Jonatan-Jose-.git
cd proyecto-intermodular-dam-25-26--Jonatan-Jose-/android_app
```

### 2. Configurar Google Maps API Key
Editar `app/src/main/AndroidManifest.xml` y reemplazar:
```xml
<meta-data
    android:name="com.google.android.geo.API_KEY"
    android:value="TU_API_KEY_AQUI" />
```

### 3. Configurar URL del backend
Editar `app/src/main/java/com/example/aplicacionmovil/data/remote/api/RetrofitClient.kt`:
```kotlin
private const val BASE_URL = "http://TU_IP_O_DOMINIO:8069/"
```

### 4. Compilar y ejecutar
```bash
./gradlew assembleDebug
```

## Generar Documentación (Dokka)

Para generar la documentación HTML del código:

```bash
./gradlew dokkaHtml
```

La documentación se genera en `app/build/dokka/`.

## Funcionalidades

### Autenticación
- Login con email/usuario y contraseña
- Registro de nuevos usuarios
- Sesión persistente con token encriptado
- Logout

### Productos
- Lista de artículos en grid con imágenes
- Búsqueda por texto
- Filtros por categoría y rango de precio
- Detalle completo del producto
- Crear nuevos artículos con múltiples imágenes
- Ver comentarios

### Compras
- Botón de compra en detalle de producto
- Historial de compras
- Historial de ventas

### Chat
- Lista de conversaciones
- Envío y recepción de mensajes
- Contactar vendedor desde producto
- Pull-to-refresh

### Mapa
- Visualización de productos con ubicación
- Marcadores interactivos
- Tarjeta de detalle al seleccionar
- Solicitud de permisos de ubicación
- Botón "Mi ubicación"

### Perfil
- Información del usuario
- Tabs: Mis artículos / Ventas / Compras
- Acceso a configuración

## API Backend

La aplicación se conecta a un backend Odoo mediante JSON-RPC 2.0:

| Endpoint | Descripción |
|----------|-------------|
| `POST /api/v1/auth/login` | Iniciar sesión |
| `POST /api/v1/auth/register` | Registrar usuario |
| `POST /api/v1/articles/list` | Listar artículos |
| `POST /api/v1/articles/{id}` | Detalle de artículo |
| `POST /api/v1/articles` | Crear artículo |
| `POST /api/v1/purchases` | Crear compra |
| `POST /api/v1/chats` | Listar/crear chats |
| `POST /api/v1/chats/{id}/messages` | Mensajes de chat |
| `POST /api/v1/categories` | Listar categorías |

## Estructura de Navegación

```
login ─────┬──> home ──────┬──> article_detail/{id}
           │               ├──> create_article
register ──┘               ├──> search
                           ├──> map
                           ├──> chat_list ──> chat_detail/{id}
                           ├──> profile ──> settings
                           └──> notifications
```

## Permisos

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

## Autores

- **Jonatan Cruz**
- **José**

Proyecto Intermodular DAM 2025-2026

## Licencia

Este proyecto es parte del trabajo académico del ciclo DAM.
