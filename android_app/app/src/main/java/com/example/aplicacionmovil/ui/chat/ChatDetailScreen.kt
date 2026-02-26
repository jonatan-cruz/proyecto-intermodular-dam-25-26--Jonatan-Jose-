package com.example.aplicacionmovil.ui.chat

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.example.aplicacionmovil.domain.models.ChatMessage
import kotlinx.coroutines.launch

/**
 * Pantalla de detalle de chat (conversación)
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatDetailScreen(
    navController: NavController,
    chatId: Int
) {
    val context = LocalContext.current
    val viewModel: ChatViewModel = viewModel(factory = ChatViewModelFactory(context))
    val chatDetailState by viewModel.chatDetailState.collectAsState()
    val sendMessageState by viewModel.sendMessageState.collectAsState()

    var messageText by remember { mutableStateOf("") }
    val listState = rememberLazyListState()
    val coroutineScope = rememberCoroutineScope()

    // Cargar mensajes al entrar
    LaunchedEffect(chatId) {
        viewModel.loadChatMessages(chatId)
    }

    // Scroll al final cuando hay nuevos mensajes
    LaunchedEffect(chatDetailState) {
        if (chatDetailState is ChatDetailState.Success) {
            val messages = (chatDetailState as ChatDetailState.Success).messages
            if (messages.isNotEmpty()) {
                coroutineScope.launch {
                    listState.animateScrollToItem(messages.size - 1)
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    when (val state = chatDetailState) {
                        is ChatDetailState.Success -> {
                            val chatInfo = state.chatInfo

                            Column {
                                Text(
                                    text = "Chat",
                                    style = MaterialTheme.typography.titleMedium,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                                chatInfo?.articulo?.nombre?.let { articulo ->
                                    Text(
                                        text = articulo,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                }
                            }
                        }
                        else -> Text("Chat")
                    }
                },
                navigationIcon = {
                    IconButton(onClick = { navController.navigateUp() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Volver")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadChatMessages(chatId) }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refrescar")
                    }
                }
            )
        },
        bottomBar = {
            // Input de mensaje
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shadowElevation = 8.dp
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedTextField(
                        value = messageText,
                        onValueChange = { messageText = it },
                        placeholder = { Text("Escribe un mensaje...") },
                        modifier = Modifier.weight(1f),
                        shape = RoundedCornerShape(24.dp),
                        maxLines = 4,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.5f)
                        )
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    // Botón enviar
                    val isSending = sendMessageState is SendMessageState.Sending
                    FilledIconButton(
                        onClick = {
                            if (messageText.isNotBlank() && !isSending) {
                                viewModel.sendMessage(chatId, messageText)
                                messageText = ""
                            }
                        },
                        enabled = messageText.isNotBlank() && !isSending,
                        modifier = Modifier.size(48.dp)
                    ) {
                        if (isSending) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                strokeWidth = 2.dp,
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Icon(Icons.Default.Send, contentDescription = "Enviar")
                        }
                    }
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (val state = chatDetailState) {
                is ChatDetailState.Loading -> {
                    CircularProgressIndicator(
                        modifier = Modifier.align(Alignment.Center)
                    )
                }

                is ChatDetailState.Error -> {
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
                        Button(onClick = { viewModel.loadChatMessages(chatId) }) {
                            Text("Reintentar")
                        }
                    }
                }

                is ChatDetailState.Success -> {
                    if (state.messages.isEmpty()) {
                        EmptyMessagesState()
                    } else {
                        LazyColumn(
                            state = listState,
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(horizontal = 8.dp),
                            contentPadding = PaddingValues(vertical = 8.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            items(state.messages) { message ->
                                MessageBubble(
                                    message = message,
                                    isFromMe = message.isMine
                                )
                            }
                        }
                    }
                }
            }

            // Mostrar error de envío
            if (sendMessageState is SendMessageState.Error) {
                Snackbar(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(16.dp),
                    action = {
                        TextButton(onClick = { viewModel.resetSendState() }) {
                            Text("OK")
                        }
                    }
                ) {
                    Text((sendMessageState as SendMessageState.Error).message)
                }
            }
        }
    }
}

/**
 * Burbuja de mensaje
 * Estructura según backend:
 * - contenido: String
 * - fecha_envio: String?
 * - leido: Boolean
 * - usuario: {id, nombre}
 * - is_mine: Boolean
 */
@Composable
fun MessageBubble(
    message: ChatMessage,
    isFromMe: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isFromMe) Arrangement.End else Arrangement.Start
    ) {
        Card(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .padding(vertical = 2.dp),
            shape = RoundedCornerShape(
                topStart = 16.dp,
                topEnd = 16.dp,
                bottomStart = if (isFromMe) 16.dp else 4.dp,
                bottomEnd = if (isFromMe) 4.dp else 16.dp
            ),
            colors = CardDefaults.cardColors(
                containerColor = if (isFromMe) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.surfaceVariant
                }
            )
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                // Nombre del remitente (solo si no es mío)
                if (!isFromMe) {
                    message.usuario?.nombre?.let { nombre ->
                        Text(
                            text = nombre,
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                    }
                }

                // Contenido del mensaje
                Text(
                    text = message.contenido,
                    style = MaterialTheme.typography.bodyMedium,
                    color = if (isFromMe) {
                        MaterialTheme.colorScheme.onPrimary
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    }
                )

                // Hora y estado
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 4.dp),
                    horizontalArrangement = Arrangement.End,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    message.fechaEnvio?.let { fecha ->
                        Text(
                            text = formatMessageTime(fecha),
                            style = MaterialTheme.typography.labelSmall,
                            color = if (isFromMe) {
                                MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.7f)
                            } else {
                                MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                            }
                        )
                    }

                    // Indicador de leído (solo para mis mensajes)
                    if (isFromMe) {
                        Spacer(modifier = Modifier.width(4.dp))
                        Icon(
                            imageVector = if (message.leido) Icons.Default.Done else Icons.Default.Done,
                            contentDescription = if (message.leido) "Leído" else "Enviado",
                            modifier = Modifier.size(14.dp),
                            tint = if (message.leido) {
                                MaterialTheme.colorScheme.onPrimary
                            } else {
                                MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.5f)
                            }
                        )
                    }
                }
            }
        }
    }
}

/**
 * Estado vacío cuando no hay mensajes
 */
@Composable
fun EmptyMessagesState() {
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
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "Inicia la conversación",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Escribe un mensaje para comenzar",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * Formatea la hora del mensaje
 */
fun formatMessageTime(dateString: String): String {
    return try {
        if (dateString.contains("T")) {
            // Formato ISO: 2024-01-15T10:30:00
            val parts = dateString.split("T")
            if (parts.size >= 2) parts[1].take(5) else dateString
        } else if (dateString.contains(" ")) {
            val parts = dateString.split(" ")
            if (parts.size >= 2) parts[1].take(5) else dateString
        } else {
            dateString
        }
    } catch (e: Exception) {
        dateString
    }
}
