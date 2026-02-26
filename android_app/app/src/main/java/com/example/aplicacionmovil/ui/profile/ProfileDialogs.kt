package com.example.aplicacionmovil.ui.profile

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.compose.AsyncImage
import com.example.aplicacionmovil.domain.models.UpdateProfileRequest
import com.example.aplicacionmovil.domain.models.User
import com.example.aplicacionmovil.utils.ImageDisplayUtils
import com.example.aplicacionmovil.utils.ImageUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditProfileDialog(
    user: User,
    onUpdateProfile: (UpdateProfileRequest) -> Unit,
    onChangePassword: (String, String, (Boolean) -> Unit) -> Unit,
    onDeactivateAccount: (String, (Boolean) -> Unit) -> Unit,
    onDismiss: () -> Unit
) {
    // Estado local para los campos, inicializado con los datos del usuario
    var name by remember(user) { mutableStateOf(user.name) }
    var location by remember(user) { mutableStateOf(user.ciudad ?: "") }
    var phone by remember(user) { mutableStateOf(user.telefono ?: "") }
    var bio by remember(user) { mutableStateOf(user.biografia ?: "") }
    var avatarBase64 by remember(user) { mutableStateOf<String?>(user.fotoPerfil) }
    var email by remember(user) { mutableStateOf(user.email) }

    var showChangePassword by remember { mutableStateOf(false) }
    var showDeactivateAccount by remember { mutableStateOf(false) }

    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            val base64 = ImageUtils.uriToBase64(context, it)
            if (base64 != null) {
                avatarBase64 = base64
            } else {
                Toast.makeText(context, "Error al procesar la imagen", Toast.LENGTH_SHORT).show()
            }
        }
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Surface(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
            color = MaterialTheme.colorScheme.background
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
            ) {
                // Toolbar superior
                TopAppBar(
                    title = { Text("Editar Perfil") },
                    navigationIcon = {
                        IconButton(onClick = onDismiss) {
                            Icon(Icons.Default.Close, contentDescription = "Cerrar")
                        }
                    },
                    actions = {
                        TextButton(
                            onClick = {
                                onUpdateProfile(
                                    UpdateProfileRequest(
                                        name = name,
                                        ubicacion = location,
                                        telefono = phone,
                                        biografia = bio,
                                        avatar = avatarBase64,
                                        email = email
                                    )
                                )
                            }
                        ) {
                            Text("Guardar", fontWeight = FontWeight.Bold)
                        }
                    }
                )

                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .verticalScroll(rememberScrollState())
                        .padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Sección de Foto de Perfil
                    Box(
                        modifier = Modifier
                            .size(100.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.surfaceVariant)
                            .clickable { launcher.launch("image/*") },
                        contentAlignment = Alignment.Center
                    ) {
                        if (avatarBase64 != null) {
                            AsyncImage(
                                model = ImageDisplayUtils.ensureDisplayableImage(avatarBase64),
                                contentDescription = "Nueva foto de perfil",
                                modifier = Modifier.fillMaxSize(),
                                contentScale = ContentScale.Crop
                            )
                        } else {
                            Icon(
                                Icons.Default.Person,
                                contentDescription = null,
                                modifier = Modifier.size(50.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        
                        // Overlay de editar
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.3f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(Icons.Default.Edit, contentDescription = null, tint = Color.White)
                        }
                    }

                    TextButton(onClick = { launcher.launch("image/*") }) {
                        Text("Cambiar foto")
                    }

                    Spacer(modifier = Modifier.height(24.dp))

                    // Información Personal
                    SectionHeader("Información Personal")
                    OutlinedTextField(
                        value = name,
                        onValueChange = { name = it },
                        label = { Text("Nombre") },
                        modifier = Modifier.fillMaxWidth(),
                        leadingIcon = { Icon(Icons.Default.Person, null) }
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = location,
                        onValueChange = { location = it },
                        label = { Text("Ubicación") },
                        modifier = Modifier.fillMaxWidth(),
                        leadingIcon = { Icon(Icons.Default.LocationOn, null) }
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = phone,
                        onValueChange = { phone = it },
                        label = { Text("Teléfono") },
                        modifier = Modifier.fillMaxWidth(),
                        leadingIcon = { Icon(Icons.Default.Phone, null) }
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    OutlinedTextField(
                        value = bio,
                        onValueChange = { bio = it },
                        label = { Text("Biografía") },
                        modifier = Modifier.fillMaxWidth(),
                        minLines = 3,
                        maxLines = 5
                    )

                    Spacer(modifier = Modifier.height(32.dp))

                    // Gestión de Correo
                    SectionHeader("Gestionar Correo")
                    OutlinedTextField(
                        value = email,
                        onValueChange = { email = it },
                        label = { Text("Email / Login") },
                        modifier = Modifier.fillMaxWidth(),
                        leadingIcon = { Icon(Icons.Default.Email, null) }
                    )
                    Text(
                        "Este correo se usará para iniciar sesión.",
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.align(Alignment.Start).padding(top = 4.dp)
                    )

                    Spacer(modifier = Modifier.height(32.dp))

                    // Seguridad
                    SectionHeader("Seguridad")
                    Button(
                        onClick = { showChangePassword = true },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(
                            containerColor = MaterialTheme.colorScheme.secondaryContainer,
                            contentColor = MaterialTheme.colorScheme.onSecondaryContainer
                        )
                    ) {
                        Icon(Icons.Default.Lock, null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Cambiar Contraseña")
                    }

                    Spacer(modifier = Modifier.height(48.dp))

                    // Zona de Peligro
                    SectionHeader("Zona de Peligro", color = MaterialTheme.colorScheme.error)
                    OutlinedButton(
                        onClick = { showDeactivateAccount = true },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error),
                    ) {
                        Icon(Icons.Default.Delete, null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Desactivar Cuenta")
                    }
                    
                    Spacer(modifier = Modifier.height(32.dp))
                }
            }
        }
    }

    if (showChangePassword) {
        ChangePasswordDialog(
            onConfirm = { current, new, onComplete ->
                onChangePassword(current, new) { success ->
                    if (success) showChangePassword = false
                    onComplete(success)
                }
            },
            onDismiss = { showChangePassword = false }
        )
    }

    if (showDeactivateAccount) {
        DeactivateAccountDialog(
            onConfirm = { password, onComplete ->
                onDeactivateAccount(password) { success ->
                    if (success) showDeactivateAccount = false
                    onComplete(success)
                }
            },
            onDismiss = { showDeactivateAccount = false }
        )
    }
}

@Composable
fun SectionHeader(title: String, color: Color = MaterialTheme.colorScheme.primary) {
    Column(modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)) {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium,
            color = color,
            fontWeight = FontWeight.Bold
        )
        Divider(color = color.copy(alpha = 0.5f))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChangePasswordDialog(
    onConfirm: (String, String, (Boolean) -> Unit) -> Unit,
    onDismiss: () -> Unit
) {
    var currentPassword by remember { mutableStateOf("") }
    var newPassword by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Cambiar Contraseña") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = currentPassword,
                    onValueChange = { currentPassword = it },
                    label = { Text("Contraseña Actual") }
                )
                OutlinedTextField(
                    value = newPassword,
                    onValueChange = { newPassword = it },
                    label = { Text("Nueva Contraseña") }
                )
                OutlinedTextField(
                    value = confirmPassword,
                    onValueChange = { confirmPassword = it },
                    label = { Text("Confirmar Nueva Contraseña") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (newPassword == confirmPassword && newPassword.isNotEmpty()) {
                        loading = true
                        onConfirm(currentPassword, newPassword) { loading = false }
                    }
                },
                enabled = !loading && newPassword == confirmPassword
            ) {
                Text("Confirmar")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !loading) {
                Text("Cancelar")
            }
        }
    )
}

@Composable
fun DeactivateAccountDialog(
    onConfirm: (String, (Boolean) -> Unit) -> Unit,
    onDismiss: () -> Unit
) {
    var password by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Desactivar Cuenta") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Esta acción desactivará tu cuenta. Por favor, introduce tu contraseña para confirmar.")
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("Contraseña") }
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    loading = true
                    onConfirm(password) { loading = false }
                },
                enabled = !loading && password.isNotEmpty(),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
            ) {
                Text("Desactivar")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss, enabled = !loading) {
                Text("Cancelar")
            }
        }
    )
}
