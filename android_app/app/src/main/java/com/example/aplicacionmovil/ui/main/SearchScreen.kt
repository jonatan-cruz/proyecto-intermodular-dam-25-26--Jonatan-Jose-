package com.example.aplicacionmovil.ui.main

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import androidx.compose.ui.graphics.Color
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreen(navController: NavController) {
    val context = LocalContext.current
    val viewModel: HomeViewModel = viewModel(
        factory = HomeViewModelFactory(context)
    )

    var searchQuery by remember { mutableStateOf("") }
    var selectedCategoryId by remember { mutableStateOf<Int?>(null) }
    var selectedCategoryName by remember { mutableStateOf<String?>(null) }
    var priceRange by remember { mutableStateOf(0f..10000f) }
    var showFilterDialog by remember { mutableStateOf(false) }
    var showPriceDialog by remember { mutableStateOf(false) }

    val articlesState by viewModel.articlesState.collectAsState()
    val categoriesState by viewModel.categoriesState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    OutlinedTextField(
                        value = searchQuery,
                        onValueChange = {
                            searchQuery = it
                            viewModel.searchArticles(it, selectedCategoryId, priceRange)
                        },
                        placeholder = { Text("Buscar...") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(end = 16.dp),
                        singleLine = true,
                        shape = RoundedCornerShape(12.dp),
                        trailingIcon = {
                            if (searchQuery.isNotEmpty()) {
                                IconButton(onClick = { searchQuery = ""; viewModel.loadArticles() }) {
                                    Icon(Icons.Default.Clear, contentDescription = "Limpiar")
                                }
                            }
                        },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = Color.Transparent,
                            focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f),
                            unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.3f)
                        )
                    )
                },
                navigationIcon = {
                    IconButton(onClick = { navController.navigateUp() }) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Volver")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Chips de filtros
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Filtro de categorías
                FilterChip(
                    selected = selectedCategoryId != null,
                    onClick = { showFilterDialog = true },
                    label = {
                        Text(
                            text = selectedCategoryName ?: "Categorías",
                            fontSize = 13.sp
                        )
                    },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.List,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                )

                // Filtro de precio
                FilterChip(
                    selected = priceRange != 0f..10000f,
                    onClick = { showPriceDialog = true },
                    label = {
                        Text(
                            text = if (priceRange != 0f..10000f) {
                                "${priceRange.start.toInt()}-${priceRange.endInclusive.toInt()}€"
                            } else {
                                "Precio"
                            },
                            fontSize = 13.sp
                        )
                    },
                    leadingIcon = {
                        Icon(
                            imageVector = Icons.Default.ShoppingCart,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                )

                // Limpiar filtros
                if (selectedCategoryId != null || priceRange != 0f..10000f || searchQuery.isNotEmpty()) {
                    FilterChip(
                        selected = false,
                        onClick = {
                            selectedCategoryId = null
                            selectedCategoryName = null
                            priceRange = 0f..10000f
                            searchQuery = ""
                            viewModel.loadArticles()
                        },
                        label = {
                            Text("Limpiar", fontSize = 13.sp)
                        },
                        leadingIcon = {
                            Icon(
                                imageVector = Icons.Default.Clear,
                                contentDescription = null,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    )
                }
            }
            when (val state = articlesState) {
                is ArticlesState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
                is ArticlesState.Success -> {
                    if (state.articles.isEmpty()) {
                        SearchEmptyState()
                    } else {
                        LazyVerticalGrid(
                            columns = GridCells.Fixed(2),
                            contentPadding = PaddingValues(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.fillMaxSize()
                        ) {
                            items(state.articles) { article: com.example.aplicacionmovil.domain.models.Article ->
                                ArticleCard(
                                    article = article,
                                    onClick = {
                                        navController.navigate("article_detail/${article.id}")
                                    }
                                )
                            }
                        }
                    }
                }
                is ArticlesState.Error -> {
                    SearchErrorState(state.message) { viewModel.loadArticles() }
                }
            }
        }
    }

    // Diálogo de filtro de categorías
    if (showFilterDialog) {
        AlertDialog(
            onDismissRequest = { showFilterDialog = false },
            title = { Text("Seleccionar Categoría") },
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
            }
        )
    }

    // Diálogo de filtro de precio
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
fun SearchEmptyState() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = Icons.Default.Search,
            contentDescription = null,
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f)
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "No encontramos resultados",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Intenta con otras palabras clave",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
fun SearchErrorState(message: String, onRetry: () -> Unit) {
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
            tint = MaterialTheme.colorScheme.error,
            modifier = Modifier.size(48.dp)
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(text = message, color = MaterialTheme.colorScheme.error, textAlign = TextAlign.Center)
        Button(onClick = onRetry) {
            Text("Reintentar")
        }
    }
}
