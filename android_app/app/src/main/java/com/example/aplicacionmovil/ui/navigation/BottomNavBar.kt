package com.example.aplicacionmovil.ui.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavController
import androidx.navigation.compose.currentBackStackEntryAsState

/**
 * Rutas de navegación para el BottomNavBar
 */
sealed class BottomNavItem(
    val route: String,
    val title: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector
) {
    object Home : BottomNavItem(
        route = "home",
        title = "Inicio",
        selectedIcon = Icons.Filled.Home,
        unselectedIcon = Icons.Outlined.Home
    )
    object Search : BottomNavItem(
        route = "search",
        title = "Buscar",
        selectedIcon = Icons.Filled.Search,
        unselectedIcon = Icons.Outlined.Search
    )
    object Map : BottomNavItem(
        route = "map",
        title = "Mapa",
        selectedIcon = Icons.Filled.LocationOn,
        unselectedIcon = Icons.Outlined.LocationOn
    )
    object Chat : BottomNavItem(
        route = "chat_list",
        title = "Chat",
        selectedIcon = Icons.Filled.Email,
        unselectedIcon = Icons.Outlined.Email
    )
    object Profile : BottomNavItem(
        route = "profile",
        title = "Perfil",
        selectedIcon = Icons.Filled.Person,
        unselectedIcon = Icons.Outlined.Person
    )
}

/**
 * Barra de navegación inferior para la app
 */
@Composable
fun BottomNavBar(navController: NavController) {
    val items = listOf(
        BottomNavItem.Home,
        BottomNavItem.Search,
        BottomNavItem.Map,
        BottomNavItem.Chat,
        BottomNavItem.Profile
    )

    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route

    // Solo mostrar en pantallas principales
    val showBottomBar = items.any { it.route == currentRoute }

    if (showBottomBar) {
        NavigationBar {
            items.forEach { item ->
                val selected = currentRoute == item.route
                NavigationBarItem(
                    icon = {
                        Icon(
                            imageVector = if (selected) item.selectedIcon else item.unselectedIcon,
                            contentDescription = item.title
                        )
                    },
                    label = { Text(item.title) },
                    selected = selected,
                    onClick = {
                        if (currentRoute != item.route) {
                            navController.navigate(item.route) {
                                // Pop hasta el inicio para evitar stack grande
                                popUpTo(navController.graph.startDestinationId) {
                                    saveState = true
                                }
                                // Evitar múltiples copias de la misma pantalla
                                launchSingleTop = true
                                // Restaurar estado al volver
                                restoreState = true
                            }
                        }
                    }
                )
            }
        }
    }
}
