package com.example.aplicacionmovil.ui.chat

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.example.aplicacionmovil.data.local.SessionManager
import com.example.aplicacionmovil.data.remote.api.RetrofitClient
import com.example.aplicacionmovil.domain.models.*
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// ==================== ESTADOS ====================

sealed class ChatsListState {
    object Loading : ChatsListState()
    data class Success(val chats: List<ChatConversation>) : ChatsListState()
    data class Error(val message: String) : ChatsListState()
}

sealed class ChatDetailState {
    object Loading : ChatDetailState()
    data class Success(
        val messages: List<ChatMessage>,
        val chatInfo: ChatInfo?
    ) : ChatDetailState()
    data class Error(val message: String) : ChatDetailState()
}

sealed class SendMessageState {
    object Idle : SendMessageState()
    object Sending : SendMessageState()
    object Success : SendMessageState()
    data class Error(val message: String) : SendMessageState()
}

// ==================== VIEWMODEL ====================

/**
 * ViewModel para gestionar la lista de chats y los mensajes
 */
class ChatViewModel(private val context: Context) : ViewModel() {

    private val api = RetrofitClient.getAuthenticatedService(context)
    private val sessionManager = SessionManager(context)

    // Estado de la lista de chats
    private val _chatsState = MutableStateFlow<ChatsListState>(ChatsListState.Loading)
    val chatsState: StateFlow<ChatsListState> = _chatsState.asStateFlow()

    // Estado del detalle del chat (mensajes)
    private val _chatDetailState = MutableStateFlow<ChatDetailState>(ChatDetailState.Loading)
    val chatDetailState: StateFlow<ChatDetailState> = _chatDetailState.asStateFlow()

    // Estado de envío de mensaje
    private val _sendMessageState = MutableStateFlow<SendMessageState>(SendMessageState.Idle)
    val sendMessageState: StateFlow<SendMessageState> = _sendMessageState.asStateFlow()

    // ID del usuario actual
    val currentUserId: Int
        get() = sessionManager.getUserId()

    init {
        loadChats()
    }

    /**
     * Carga la lista de conversaciones del usuario
     */
    fun loadChats() {
        viewModelScope.launch {
            _chatsState.value = ChatsListState.Loading
            try {
                val response = api.getMyChats()
                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        val chats = apiResponse.data?.chats ?: emptyList()
                        _chatsState.value = ChatsListState.Success(chats)
                    } else {
                        _chatsState.value = ChatsListState.Error(
                            apiResponse?.message ?: "Error al cargar conversaciones"
                        )
                    }
                } else {
                    _chatsState.value = ChatsListState.Error("Error ${response.code()}")
                }
            } catch (e: Exception) {
                _chatsState.value = ChatsListState.Error(
                    "Error de conexión: ${e.localizedMessage}"
                )
                e.printStackTrace()
            }
        }
    }

    /**
     * Carga los mensajes de un chat específico
     */
    fun loadChatMessages(chatId: Int) {
        viewModelScope.launch {
            _chatDetailState.value = ChatDetailState.Loading
            try {
                val response = api.getChatMessages(chatId)
                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        val messages = apiResponse.data?.messages ?: emptyList()
                        val chatInfo = apiResponse.data?.chatInfo
                        _chatDetailState.value = ChatDetailState.Success(messages, chatInfo)
                    } else {
                        _chatDetailState.value = ChatDetailState.Error(
                            apiResponse?.message ?: "Error al cargar mensajes"
                        )
                    }
                } else {
                    _chatDetailState.value = ChatDetailState.Error("Error ${response.code()}")
                }
            } catch (e: Exception) {
                _chatDetailState.value = ChatDetailState.Error(
                    "Error de conexión: ${e.localizedMessage}"
                )
                e.printStackTrace()
            }
        }
    }

    /**
     * Envía un mensaje en el chat
     */
    fun sendMessage(chatId: Int, contenido: String) {
        if (contenido.isBlank()) return

        viewModelScope.launch {
            _sendMessageState.value = SendMessageState.Sending
            try {
                val request = SendMessageRequest(contenido = contenido)
                val response = api.sendMessage(chatId, JsonRpcRequest(params = request))

                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        _sendMessageState.value = SendMessageState.Success
                        // Recargar mensajes después de enviar
                        loadChatMessages(chatId)
                        // Reset state after a brief delay
                        delay(100)
                        _sendMessageState.value = SendMessageState.Idle
                    } else {
                        _sendMessageState.value = SendMessageState.Error(
                            apiResponse?.message ?: "Error al enviar mensaje"
                        )
                    }
                } else {
                    _sendMessageState.value = SendMessageState.Error("Error ${response.code()}")
                }
            } catch (e: Exception) {
                _sendMessageState.value = SendMessageState.Error(
                    "Error de conexión: ${e.localizedMessage}"
                )
                e.printStackTrace()
            }
        }
    }

    /**
     * Crea un nuevo chat o obtiene uno existente sobre un artículo
     */
    fun createOrGetChat(articuloId: Int, onSuccess: (Int) -> Unit, onError: (String) -> Unit = {}) {
        viewModelScope.launch {
            try {
                val request = CreateChatRequest(articuloId = articuloId)
                val response = api.createOrGetChat(JsonRpcRequest(params = request))

                if (response.isSuccessful) {
                    val apiResponse = response.body()?.result
                    if (apiResponse?.success == true) {
                        val chatId = (apiResponse.data?.get("chat_id") as? Double)?.toInt()
                        if (chatId != null) {
                            onSuccess(chatId)
                        } else {
                            onError("No se pudo obtener el ID del chat")
                        }
                    } else {
                        onError(apiResponse?.message ?: "Error al crear chat")
                    }
                } else {
                    onError("Error ${response.code()}")
                }
            } catch (e: Exception) {
                onError("Error de conexión: ${e.localizedMessage}")
                e.printStackTrace()
            }
        }
    }

    fun refreshChats() {
        loadChats()
    }

    fun resetSendState() {
        _sendMessageState.value = SendMessageState.Idle
    }
}

// ==================== FACTORY ====================

class ChatViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ChatViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ChatViewModel(context) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
