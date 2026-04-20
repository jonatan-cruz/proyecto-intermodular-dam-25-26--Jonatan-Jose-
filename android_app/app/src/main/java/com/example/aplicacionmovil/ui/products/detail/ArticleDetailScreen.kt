package com.example.aplicacionmovil.ui.products.detail

import android.util.Base64
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Send
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.compose.AsyncImage
import androidx.navigation.NavController
import com.example.aplicacionmovil.data.local.SessionManager
import com.example.aplicacionmovil.domain.models.Article
import com.example.aplicacionmovil.domain.models.ArticleDetail
import com.example.aplicacionmovil.domain.models.ArticleImage
import com.example.aplicacionmovil.domain.models.ArticlePropietario
import com.example.aplicacionmovil.domain.models.Category
import com.example.aplicacionmovil.domain.models.ArticleTag
import com.example.aplicacionmovil.ui.main.BuyButton
import com.example.aplicacionmovil.ui.chat.ChatViewModel
import com.example.aplicacionmovil.ui.chat.ChatViewModelFactory
import com.example.aplicacionmovil.utils.DateUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArticleDetailScreen(
    navController: NavController,
    articleId: Int
) {
    val context = LocalContext.current
    val viewModel: ArticleDetailViewModel = viewModel(
        factory = ArticleDetailViewModelFactory(context)
    )
    val chatViewModel: ChatViewModel = viewModel(
        factory = ChatViewModelFactory(context)
    )
    val state by viewModel.state.collectAsState()

    LaunchedEffect(articleId) {
        viewModel.loadArticleDetail(articleId)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Detalle del Producto") },
                navigationIcon = {
                    IconButton(onClick = { navController.navigateUp() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Volver")
                    }
                }
            )
        }
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            when (val currentState = state) {
                is ArticleDetailState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }
                is ArticleDetailState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxSize().padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(text = currentState.message, color = MaterialTheme.colorScheme.error)
                        Button(onClick = { viewModel.loadArticleDetail(articleId) }) {
                            Text("Reintentar")
                        }
                    }
                }
                is ArticleDetailState.Success -> {
                    ArticleDetailContent(
                        article = currentState.article,
                        context = context,
                        navController = navController,
                        chatViewModel = chatViewModel
                    )
                }
            }
        }
    }
}

/**
 * Convierte un ArticleDetail (pantalla de detalle) en un Article (modelo de lista)
 * para poder reutilizar el BuyButton sin duplicar lógica.
 */
fun ArticleDetail.toArticle(): Article = Article(
    id = id,
    codigo = codigo,
    nombre = nombre,
    descripcion = descripcion,
    precio = precio,
    estadoProducto = estadoProducto,
    estadoPublicacion = estadoPublicacion,
    localidad = localidad,
    latitud = latitud,
    longitud = longitud,
    categoria = categoria?.let { Category(id = it.id, nombre = it.nombre) },
    propietario = propietario?.let {
        ArticlePropietario(id = it.id, nombre = it.nombre, calificacionPromedio = it.calificacionPromedio)
    },
    etiquetas = etiquetas.map { ArticleTag(id = it.id, nombre = it.nombre) }
)

@Composable
fun ArticleDetailContent(
    article: ArticleDetail,
    context: android.content.Context,
    navController: NavController,
    chatViewModel: ChatViewModel
) {
    val currentUserId = remember { SessionManager(context).getUserId() }
    val isOwner = article.propietario?.id == currentUserId

    // Estado para el botón de contactar
    var isCreatingChat by remember { mutableStateOf(false) }
    var chatError by remember { mutableStateOf<String?>(null) }

    LazyColumn(
        modifier = Modifier.fillMaxSize()
    ) {
        // Galería de imágenes (simplificada a la primera por ahora o scroll horizontal)
        item {
            ArticleImageHeader(article.imagenes)
        }

        item {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = article.nombre,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.weight(1f)
                    )
                    Text(
                        text = "%.2f €".format(article.precio),
                        style = MaterialTheme.typography.headlineSmall,
                        color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold
                    )

                }

                Spacer(modifier = Modifier.height(8.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Badge(
                        containerColor = when (article.estadoProducto.lowercase()) {
                            "nuevo" -> Color(0xFF4CAF50)
                            "como nuevo" -> Color(0xFF8BC34A)
                            "buen estado" -> Color(0xFFFFC107)
                            else -> Color(0xFFFF9800)
                        }
                    ) {
                        Text(article.estadoProducto.uppercase(), modifier = Modifier.padding(4.dp), color = Color.White)
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = article.categoria?.nombre ?: "Sin categoría",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        // Ubicación y Fecha
        item {
            Column(modifier = Modifier.padding(horizontal = 16.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.LocationOn,
                        contentDescription = null,
                        modifier = Modifier.size(18.dp),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = article.localidad ?: "Ubicación no disponible",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                article.createDate?.let { date ->
                    Text(
                        text = "Publicado: ${DateUtils.formatLongDate(date)}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }

        // Etiquetas
        if (article.etiquetas.isNotEmpty()) {
            item {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Etiquetas",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        article.etiquetas.forEach { tag ->
                            SuggestionChip(
                                onClick = { },
                                label = { Text(tag.nombre) }
                            )
                        }
                    }
                }
            }
        }

        item {
            Column(modifier = Modifier.padding(16.dp)) {
                HorizontalDivider()
                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "Descripción",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = article.descripcion,
                    style = MaterialTheme.typography.bodyLarge
                )

                Spacer(modifier = Modifier.height(24.dp))
                HorizontalDivider()
                Spacer(modifier = Modifier.height(16.dp))

                // Propietario
                article.propietario?.let { owner ->
                    Text(
                        text = "Vendedor",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f))
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Surface(
                                modifier = Modifier.size(48.dp),
                                shape = CircleShape,
                                color = MaterialTheme.colorScheme.primary.copy(alpha = 0.1f)
                            ) {
                                Icon(
                                    Icons.Default.Person,
                                    contentDescription = null,
                                    modifier = Modifier.padding(8.dp),
                                    tint = MaterialTheme.colorScheme.primary
                                )
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column {
                                Text(text = owner.nombre, fontWeight = FontWeight.Bold)
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        Icons.Default.Star,
                                        contentDescription = null,
                                        modifier = Modifier.size(16.dp),
                                        tint = Color(0xFFFFB300)
                                    )
                                    Text(
                                        text = " ${String.format("%.1f", owner.calificacionPromedio ?: 0.0)} (${owner.totalValoraciones ?: 0})",
                                        style = MaterialTheme.typography.bodySmall
                                    )
                                }
                            }
                        }
                    }

                    // Botón Contactar vendedor (solo si no es el propietario)
                    if (!isOwner) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(
                            onClick = {
                                isCreatingChat = true
                                chatError = null
                                chatViewModel.createOrGetChat(
                                    articuloId = article.id,
                                    onSuccess = { chatId ->
                                        isCreatingChat = false
                                        navController.navigate("chat_detail/$chatId")
                                    },
                                    onError = { error ->
                                        isCreatingChat = false
                                        chatError = error
                                    }
                                )
                            },
                            enabled = !isCreatingChat,
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.secondary
                            )
                        ) {
                            if (isCreatingChat) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    strokeWidth = 2.dp,
                                    color = MaterialTheme.colorScheme.onSecondary
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                            } else {
                                Icon(
                                    imageVector = Icons.Filled.Send,
                                    contentDescription = null,
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                            }
                            Text("Contactar vendedor")
                        }

                        // Mostrar error si existe
                        chatError?.let { error ->
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = error,
                                color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))


                // Comentarios
                if (article.comentarios.isNotEmpty()) {
                    HorizontalDivider()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = "Comentarios (${article.conteoComentarios})",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    article.comentarios.forEach { comment ->
                        Card(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text(
                                    text = comment.emisor.nombre,
                                    fontWeight = FontWeight.Bold,
                                    style = MaterialTheme.typography.bodyMedium
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(text = comment.texto, style = MaterialTheme.typography.bodyLarge)
                                if (comment.fechaHora != null) {
                                    Text(
                                        text = DateUtils.formatRelativeTime(comment.fechaHora),
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.6f),
                                        modifier = Modifier.align(Alignment.End)
                                    )
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }

        // ─── Botón de compra ───
        item {
            // Solo mostramos el botón si el artículo está publicado
            if (article.estadoPublicacion == "publicado") {
                Box(modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp)) {
                    BuyButton(
                        article = article.toArticle(),
                        isOwner = isOwner,
                        compact = false
                    )
                }
                Spacer(modifier = Modifier.height(24.dp))
            }
        }
    }
}

@Composable
fun ArticleImageHeader(imagenes: List<ArticleImage>) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(300.dp)
            .background(MaterialTheme.colorScheme.surfaceVariant)
    ) {
        if (imagenes.isNotEmpty()) {
            val imageBase64 = imagenes.first().image
            if (imageBase64 != null) {
                val imageBytes = remember(imageBase64) {
                    try {
                        Base64.decode(imageBase64, Base64.DEFAULT)
                    } catch (e: Exception) {
                        null
                    }
                }
                AsyncImage(
                    model = imageBytes,
                    contentDescription = null,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            }
        } else {
            Icon(
                Icons.Default.ShoppingCart,
                contentDescription = null,
                modifier = Modifier.size(100.dp).align(Alignment.Center),
                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.2f)
            )
        }
    }
}

