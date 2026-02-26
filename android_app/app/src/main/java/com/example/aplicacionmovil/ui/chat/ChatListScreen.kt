package com.example.aplicacionmovil.ui.chat

import android.util.Base64
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import coil.compose.AsyncImage
import com.example.aplicacionmovil.domain.models.ChatConversation

/**
 * Pantalla de lista de conversaciones
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatListScreen(navController: NavController) {
    val context = LocalContext.current
    val viewModel: ChatViewModel = viewModel(factory = ChatViewModelFactory(context))
    val chatsState by viewModel.chatsState.collectAsState()

    // Estado para pull-to-refresh
    val isRefreshing = chatsState is ChatsListState.Loading

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Mensajes") },
                actions = {
                    IconButton(onClick = { viewModel.refreshChats() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refrescar")
                    }
                }
            )
        }
    ) { padding ->
        PullToRefreshBox(
            isRefreshing = isRefreshing,
            onRefresh = { viewModel.refreshChats() },
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (val state = chatsState) {
                is ChatsListState.Loading -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator()
                    }
                }

                is ChatsListState.Error -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Warning,
                            contentDescription = null,
                            modifier = Modifier.size(64.dp),
                            tint = MaterialTheme.colorScheme.error
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = state.message,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.error
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { viewModel.refreshChats() }) {
                            Text("Reintentar")
                        }
                    }
                }

                is ChatsListState.Success -> {
                    if (state.chats.isEmpty()) {
                        EmptyChatsState()
                    } else {
                        LazyColumn(
                            modifier = Modifier.fillMaxSize(),
                            contentPadding = PaddingValues(vertical = 8.dp)
                        ) {
                            items(state.chats) { chat ->
                                ChatItem(
                                    chat = chat,
                                    onClick = {
                                        navController.navigate("chat_detail/${chat.id}")
                                    }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

/**
 * Item de chat en la lista
 * Estructura según respuesta del backend:
 * - otro_usuario: {id, nombre}
 * - articulo: {id, nombre, precio}
 */
@Composable
fun ChatItem(
    chat: ChatConversation,
    onClick: () -> Unit
) {
    val otherUserName = chat.otroUsuario?.nombre ?: "Usuario"
    val articleName = chat.articulo?.nombre ?: "Artículo"

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp)
            .clickable { onClick() },
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Avatar del otro usuario
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primaryContainer)
            ) {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = null,
                    modifier = Modifier
                        .size(32.dp)
                        .align(Alignment.Center),
                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            // Información del chat
            Column(modifier = Modifier.weight(1f)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = otherUserName,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )

                    chat.fechaUltimoMensaje?.let { fecha ->
                        Text(
                            text = formatChatDate(fecha),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }

                Spacer(modifier = Modifier.height(2.dp))

                // Nombre del artículo
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = Icons.Default.ShoppingCart,
                        contentDescription = null,
                        modifier = Modifier.size(14.dp),
                        tint = MaterialTheme.colorScheme.primary
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = articleName,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.primary,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    chat.articulo?.precio?.let { precio ->
                        Text(
                            text = " - ${precio}€",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                // Último mensaje
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = chat.ultimoMensaje ?: "Sin mensajes",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f)
                    )

                    // Contador de mensajes
                    if (chat.conteoMensajes > 0) {
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "${chat.conteoMensajes} mensajes",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

/**
 * Estado vacío cuando no hay chats
 */
@Composable
fun EmptyChatsState() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.Email,
            contentDescription = null,
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "No tienes conversaciones",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Cuando contactes con un vendedor o alguien te escriba, aparecerá aquí",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * Formatea la fecha del chat para mostrar
 */
fun formatChatDate(dateString: String): String {
    return try {
        // Simplificación: mostrar solo la hora o fecha corta
        if (dateString.contains("T")) {
            // Formato ISO: 2024-01-15T10:30:00
            val parts = dateString.split("T")
            if (parts.size >= 2) parts[1].take(5) else dateString.take(10)
        } else if (dateString.contains(" ")) {
            val parts = dateString.split(" ")
            if (parts.size >= 2) parts[1].take(5) else dateString.take(10)
        } else {
            dateString.take(10)
        }
    } catch (e: Exception) {
        dateString.take(10)
    }
}
