package com.example.aplicacionmovil.ui.products.create

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.bumptech.glide.integration.compose.ExperimentalGlideComposeApi
import com.bumptech.glide.integration.compose.GlideImage
import com.example.aplicacionmovil.ui.products.create.CategoriesFormState
import com.example.aplicacionmovil.ui.products.create.CreateArticleUiState
import com.example.aplicacionmovil.ui.products.create.CreateArticleViewModel
import com.example.aplicacionmovil.ui.products.create.CreateArticleViewModelFactory

@OptIn(ExperimentalMaterial3Api::class, ExperimentalGlideComposeApi::class)
@Composable
fun CreateArticleScreen(
    navController: NavController
) {
    val context = LocalContext.current
    val viewModel: CreateArticleViewModel = viewModel(
        factory = CreateArticleViewModelFactory(context)
    )
    val uiState by viewModel.uiState.collectAsState()
    val name by viewModel.name.collectAsState()
    val description by viewModel.description.collectAsState()
    val price by viewModel.price.collectAsState()
    val categoryId by viewModel.categoryId.collectAsState()
    val selectedImages by viewModel.selectedImages.collectAsState()
    val categoriesState by viewModel.categoriesState.collectAsState()

    val galleryLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetMultipleContents()
    ) { uris ->
        viewModel.onImagesSelected(uris)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Publicar Artículo") },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Volver")
                    }
                }
            )
        }
    ) { paddingValues ->
        Box(modifier = Modifier
            .fillMaxSize()
            .padding(paddingValues)) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Sección de Imágenes
                Text("Imágenes", fontWeight = FontWeight.Bold, fontSize = 16.sp)

                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp)
                ) {
                    item {
                        Box(
                            modifier = Modifier
                                .size(120.dp)
                                .clip(RoundedCornerShape(8.dp))
                                .background(MaterialTheme.colorScheme.surfaceVariant)
                                .clickable { galleryLauncher.launch("image/*") },
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Icon(Icons.Default.Add, contentDescription = null)
                                Text("Añadir", fontSize = 12.sp)
                            }
                        }
                    }

                    items(selectedImages) { uri ->
                        Box(modifier = Modifier.size(120.dp)) {
                            GlideImage(
                                model = uri,
                                contentDescription = null,
                                modifier = Modifier
                                    .fillMaxSize()
                                    .clip(RoundedCornerShape(8.dp)),
                                contentScale = ContentScale.Crop
                            )

                            IconButton(
                                onClick = { viewModel.removeImage(uri) },
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .padding(4.dp)
                                    .size(24.dp)
                                    .background(Color.Black.copy(alpha = 0.5f), CircleShape)
                            ) {
                                Icon(
                                    Icons.Default.Close,
                                    contentDescription = "Eliminar",
                                    tint = Color.White,
                                    modifier = Modifier.size(16.dp)
                                )
                            }
                        }
                    }
                }

                // Formulario
                OutlinedTextField(
                    value = name,
                    onValueChange = { viewModel.name.value = it },
                    label = { Text("Nombre del artículo") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = description,
                    onValueChange = { viewModel.description.value = it },
                    label = { Text("Descripción") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp),
                    singleLine = false,
                    maxLines = 5
                )

                OutlinedTextField(
                    value = price,
                    onValueChange = { viewModel.price.value = it },
                    label = { Text("Precio (€)") },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true
                )

                // Selector de Categoría Dinámico
                Text("Categoría", fontWeight = FontWeight.Bold)

                when (val state = categoriesState) {
                    is CategoriesFormState.Loading -> {
                        LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    }
                    is CategoriesFormState.Error -> {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = state.message,
                                color = MaterialTheme.colorScheme.error,
                                fontSize = 13.sp
                            )
                            TextButton(onClick = { viewModel.loadCategories() }) {
                                Text("Reintentar")
                            }
                        }
                    }
                    is CategoriesFormState.Success -> {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .horizontalScroll(rememberScrollState()),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            for (category in state.categories) {
                                FilterChip(
                                    selected = categoryId == category.id,
                                    onClick = { viewModel.categoryId.value = category.id },
                                    label = { Text(category.displayName) }
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(24.dp))

                Button(
                    onClick = {
                        viewModel.createArticle(context) {
                            navController.popBackStack()
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    enabled = uiState !is CreateArticleUiState.Loading
                ) {
                    if (uiState is CreateArticleUiState.Loading) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            color = Color.White
                        )
                    } else {
                        Text("Publicar")
                    }
                }

                if (uiState is CreateArticleUiState.Error) {
                    Text(
                        text = (uiState as CreateArticleUiState.Error).message,
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(top = 8.dp)
                    )
                }
            }
        }
    }
}
