package com.example.aplicacionmovil.ui.main

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import android.util.Base64
import androidx.compose.foundation.Image
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.res.painterResource
import coil.compose.AsyncImage
import com.example.aplicacionmovil.R
import com.example.aplicacionmovil.domain.models.Article
import com.example.aplicacionmovil.utils.ImageDisplayUtils

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    navController: NavHostController
) {
    val context = LocalContext.current
    val viewModel: HomeViewModel = viewModel(
        factory = HomeViewModelFactory(context)
    )

    var searchQuery by remember { mutableStateOf("") }
    var showFilterDialog by remember { mutableStateOf(false) }
    var selectedCategoryId by remember { mutableStateOf<Int?>(null) }
    var selectedCategoryName by remember { mutableStateOf<String?>(null) }
    var priceRange by remember { mutableStateOf(0f..10000f) }
    var showPriceDialog by remember { mutableStateOf(false) }

    val articlesState by viewModel.articlesState.collectAsState()
    val userState by viewModel.userState.collectAsState()
    val categoriesState by viewModel.categoriesState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Hola, ${userState?.name?.split(" ")?.firstOrNull() ?: "Usuario"}!",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                        Text(
                            text = "Descubre tesoros hoy",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                },
                navigationIcon = {
                    Image(
                        painter = painterResource(id = R.mipmap.ic_launcher_foreground),
                        contentDescription = "Logo",
                        modifier = Modifier
                            .size(70.dp)
                            .padding(start = 8.dp),
                        contentScale = ContentScale.Fit
                    )
                },
                actions = {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(end = 8.dp)
                    ) {
                        // Avatar de usuario
                        Box(
                            modifier = Modifier
                                .size(40.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.primaryContainer)
                                .clickable { navController.navigate("profile") },
                            contentAlignment = Alignment.Center
                        ) {
                            if (userState?.fotoPerfil != null) {
                                AsyncImage(
                                    model = userState?.fotoPerfil,
                                    contentDescription = "Foto de perfil",
                                    modifier = Modifier.fillMaxSize(),
                                    contentScale = ContentScale.Crop
                                )
                            } else if (userState?.name?.isNotEmpty() == true) {
                                Text(
                                    text = userState?.name?.firstOrNull()?.uppercase() ?: "U",
                                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 18.sp
                                )
                            } else {
                                Icon(
                                    imageVector = Icons.Default.Person,
                                    contentDescription = "Usuario",
                                    tint = MaterialTheme.colorScheme.onPrimaryContainer
                                )
                            }
                        }

                        Spacer(modifier = Modifier.width(8.dp))

                        // Botón de ajustes
                        IconButton(onClick = { navController.navigate("settings") }) {
                            Icon(
                                imageVector = Icons.Default.Settings,
                                contentDescription = "Ajustes"
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { navController.navigate("create_article") },
                icon = { Icon(Icons.Default.Add, "Publicar") },
                text = { },
                containerColor = MaterialTheme.colorScheme.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
                shape = RoundedCornerShape(20.dp),
                elevation = FloatingActionButtonDefaults.elevation(defaultElevation = 6.dp)
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(MaterialTheme.colorScheme.background)
        ) {
            // Sección de Búsqueda Premium
            Surface(
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.surface,
                shadowElevation = 0.dp
            ) {
                Column(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = {
                            searchQuery = it
                            viewModel.searchArticles(it, selectedCategoryId, priceRange)
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .shadow(4.dp, RoundedCornerShape(32.dp)),
                        placeholder = { Text("Busca lo que necesites...") },
                        leadingIcon = {
                            Icon(Icons.Default.Search, null, tint = MaterialTheme.colorScheme.primary)
                        },
                        trailingIcon = {
                            if (searchQuery.isNotEmpty()) {
                                IconButton(onClick = { searchQuery = ""; viewModel.loadArticles() }) {
                                    Icon(Icons.Default.Clear, null)
                                }
                            }
                        },
                        singleLine = true,
                        shape = RoundedCornerShape(32.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = Color.Transparent,
                            focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                            unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
                        )
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    LazyRow(
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        item {
                            FilterChip(
                                selected = selectedCategoryId != null,
                                onClick = { showFilterDialog = true },
                                label = { Text(selectedCategoryName ?: "Categorías") },
                                leadingIcon = { Icon(Icons.Default.List, null, modifier = Modifier.size(18.dp)) },
                                shape = RoundedCornerShape(20.dp)
                            )
                        }
                        item {
                            FilterChip(
                                selected = priceRange != 0f..10000f,
                                onClick = { showPriceDialog = true },
                                label = { Text("Rango de Precio") },
                                leadingIcon = { Icon(Icons.Default.ShoppingCart, null, modifier = Modifier.size(18.dp)) },
                                shape = RoundedCornerShape(20.dp)
                            )
                        }
                        if (selectedCategoryId != null || priceRange != 0f..10000f) {
                            item {
                                IconButton(
                                    onClick = { 
                                        selectedCategoryId = null; selectedCategoryName = null; 
                                        priceRange = 0f..10000f; viewModel.loadArticles() 
                                    },
                                    modifier = Modifier.clip(CircleShape).background(MaterialTheme.colorScheme.errorContainer)
                                ) {
                                    Icon(Icons.Default.Delete, null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(18.dp))
                                }
                            }
                        }
                    }
                }
            }

            // Lista de Artículos
            when (val state = articlesState) {
                is ArticlesState.Loading -> {
                    Box(Modifier.fillMaxSize(), Alignment.Center) { CircularProgressIndicator(color = MaterialTheme.colorScheme.primary) }
                }
                is ArticlesState.Success -> {
                    if (state.articles.isEmpty()) {
                        HomeEmptyState()
                    } else {
                        LazyVerticalGrid(
                            columns = GridCells.Fixed(2),
                            contentPadding = PaddingValues(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(16.dp),
                            verticalArrangement = Arrangement.spacedBy(16.dp),
                            modifier = Modifier.fillMaxSize()
                        ) {
                            items(state.articles) { article: com.example.aplicacionmovil.domain.models.Article ->
                                ArticleCard(
                                    article = article,
                                    onClick = { navController.navigate("article_detail/${article.id}") }
                                )
                            }
                        }
                    }
                }
                is ArticlesState.Error -> {
                    HomeErrorState(message = state.message) { viewModel.loadArticles() }
                }
            }
        }
    }

    // Diálogos de filtrado
    if (showFilterDialog) {
        AlertDialog(
            onDismissRequest = { showFilterDialog = false },
            title = { Text("Seleccionar Categoría", fontWeight = FontWeight.Bold) },
            text = {
                when (val state = categoriesState) {
                    is CategoriesState.Success -> {
                        LazyRow(
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            contentPadding = PaddingValues(vertical = 8.dp)
                        ) {
                            item {
                                CategoryChip(
                                    name = "Todas",
                                    isSelected = selectedCategoryId == null,
                                    onClick = {
                                        selectedCategoryId = null
                                        selectedCategoryName = null
                                        viewModel.searchArticles(searchQuery, null, priceRange)
                                        showFilterDialog = false
                                    }
                                )
                            }
                            items(state.categories) { category: com.example.aplicacionmovil.domain.models.Category ->
                                CategoryChip(
                                    name = category.displayName,
                                    count = category.conteoArticulos,
                                    isSelected = selectedCategoryId == category.id,
                                    onClick = {
                                        selectedCategoryId = category.id
                                        selectedCategoryName = category.displayName
                                        viewModel.searchArticles(searchQuery, category.id, priceRange)
                                        showFilterDialog = false
                                    }
                                )
                            }
                        }
                    }
                    is CategoriesState.Error -> {
                        Text(text = state.message, color = MaterialTheme.colorScheme.error)
                    }
                    else -> {
                        Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator()
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showFilterDialog = false }) {
                    Text("Cerrar")
                }
            },
            shape = RoundedCornerShape(28.dp)
        )
    }

    if (showPriceDialog) {
        PriceFilterDialog(
            initialRange = priceRange,
            onDismiss = { showPriceDialog = false },
            onApply = { newRange ->
                priceRange = newRange
                viewModel.searchArticles(searchQuery, selectedCategoryId, newRange)
                showPriceDialog = false
            }
        )
    }
}






@Composable
fun HomeEmptyState() {
    Column(
        Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(Icons.Default.Search, null, Modifier.size(80.dp), tint = MaterialTheme.colorScheme.primary.copy(0.2f))
        Text("No hay nada por aquí", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        Text("Prueba con otros filtros", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun HomeErrorState(message: String, onRetry: () -> Unit) {
    Column(
        Modifier.fillMaxSize().padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(Icons.Default.Warning, null, Modifier.size(64.dp), tint = MaterialTheme.colorScheme.error)
        Text("¡Ups! Algo salió mal", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.error)
        Text(message, textAlign = TextAlign.Center, style = MaterialTheme.typography.bodySmall)
        Button(onRetry, modifier = Modifier.padding(top = 16.dp), shape = RoundedCornerShape(12.dp)) {
            Text("Reintentar")
        }
    }
}