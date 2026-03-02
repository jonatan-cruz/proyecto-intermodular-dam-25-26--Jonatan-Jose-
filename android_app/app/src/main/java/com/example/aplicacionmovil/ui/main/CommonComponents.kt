package com.example.aplicacionmovil.ui.main

import android.util.Base64
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.example.aplicacionmovil.domain.models.Article

@Composable
fun ArticleCard(
    article: Article,
    onClick: () -> Unit,
    isOwner: Boolean = false
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(160.dp)
            ) {
                val imageModel: Any? = when {
                    // Primero: URL directa al endpoint de imagen (lista del home)
                    article.imagenUrl != null -> "http://10.0.2.2:8069${article.imagenUrl}"
                    // Fallback: base64 (detalle u otras pantallas)
                    article.imagenPrincipal != null -> remember(article.imagenPrincipal) {
                        try { android.util.Base64.decode(article.imagenPrincipal, android.util.Base64.DEFAULT) } catch (e: Exception) { null }
                    }
                    else -> null
                }

                if (imageModel != null) {
                    AsyncImage(
                        model = imageModel,
                        contentDescription = article.nombre,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop
                    )
                } else {
                    Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.surfaceVariant), Alignment.Center) {
                        Icon(Icons.Default.ShoppingCart, null, modifier = Modifier.size(48.dp), tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(0.3f))
                    }
                }

                // Precio flotante estilo Premium
                Surface(
                    modifier = Modifier.align(Alignment.BottomStart).padding(8.dp),
                    color = MaterialTheme.colorScheme.primary,
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        text = "%.2f€".format(article.precio),
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        color = MaterialTheme.colorScheme.onPrimary,
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    text = article.nombre ?: "Sin título",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    modifier = Modifier.padding(top = 4.dp)
                ) {
                    Icon(Icons.Default.LocationOn, null, modifier = Modifier.size(12.dp), tint = MaterialTheme.colorScheme.primary)
                    Text(
                        text = article.localidad ?: "Varias",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))
                
                // Botón de acción rápido
                Surface(
                    modifier = Modifier.fillMaxWidth().height(32.dp),
                    color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = if (isOwner) "Gestionar" else "Ver Detalle",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun CategoryChip(
    name: String,
    isSelected: Boolean,
    onClick: () -> Unit,
    count: Int? = null
) {
    Surface(
        onClick = onClick,
        color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
        shape = RoundedCornerShape(16.dp),
        border = if (isSelected) null else BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.2f)),
        modifier = Modifier.padding(vertical = 4.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = name,
                style = MaterialTheme.typography.labelLarge,
                color = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
            )
            if (count != null) {
                Spacer(modifier = Modifier.width(8.dp))
                Surface(
                    color = if (isSelected) MaterialTheme.colorScheme.onPrimary.copy(alpha = 0.2f) else MaterialTheme.colorScheme.primary.copy(alpha = 0.1f),
                    shape = CircleShape,
                ) {
                    Text(
                        text = count.toString(),
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                        style = MaterialTheme.typography.labelSmall,
                        color = if (isSelected) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}

@Composable
fun PriceFilterDialog(
    initialRange: ClosedFloatingPointRange<Float>,
    onDismiss: () -> Unit,
    onApply: (ClosedFloatingPointRange<Float>) -> Unit
) {
    var currentRange by remember { mutableStateOf(initialRange) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Rango de Precio", fontWeight = FontWeight.Bold) },
        text = {
            Column(modifier = Modifier.fillMaxWidth().padding(vertical = 16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("${currentRange.start.toInt()}€", style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    Text("${currentRange.endInclusive.toInt()}€", style = MaterialTheme.typography.bodyLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                }
                RangeSlider(
                    value = currentRange,
                    onValueChange = { currentRange = it },
                    valueRange = 0f..1000f,
                    modifier = Modifier.fillMaxWidth(),
                    colors = SliderDefaults.colors(
                        thumbColor = MaterialTheme.colorScheme.primary,
                        activeTrackColor = MaterialTheme.colorScheme.primary,
                        inactiveTrackColor = MaterialTheme.colorScheme.surfaceVariant
                    )
                )
            }
        },
        confirmButton = {
            Button(
                onClick = { onApply(currentRange) },
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Aplicar")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancelar")
            }
        },
        shape = RoundedCornerShape(28.dp)
    )
}
