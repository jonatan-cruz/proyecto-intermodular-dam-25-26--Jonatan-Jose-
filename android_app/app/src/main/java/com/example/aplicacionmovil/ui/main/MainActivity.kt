package com.example.aplicacionmovil.ui.main

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.remember
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.example.aplicacionmovil.ui.products.create.CreateArticleScreen
import com.example.aplicacionmovil.ui.theme.AplicacionMovilTheme
import com.example.aplicacionmovil.ui.products.detail.ArticleDetailScreen
import androidx.navigation.NavType
import androidx.navigation.navArgument
import com.example.aplicacionmovil.ui.profile.ProfileScreen
import com.example.aplicacionmovil.ui.settings.SettingsScreen
import com.example.aplicacionmovil.ui.navigation.BottomNavBar
import com.example.aplicacionmovil.ui.map.MapScreen
import com.example.aplicacionmovil.ui.chat.ChatListScreen
import com.example.aplicacionmovil.ui.chat.ChatDetailScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // Instala la splash screen ANTES de super.onCreate
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AplicacionMovilTheme {
                val navController = rememberNavController()
                val sessionManager = remember { com.example.aplicacionmovil.data.local.SessionManager(this@MainActivity) }
                val startDestination = if (sessionManager.fetchAuthToken() != null) "home" else "login"

                // Pantallas donde mostrar el BottomNavBar
                val navBackStackEntry by navController.currentBackStackEntryAsState()
                val currentRoute = navBackStackEntry?.destination?.route
                val showBottomBar = currentRoute in listOf("home", "search", "map", "chat_list", "profile")

                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    bottomBar = {
                        if (showBottomBar) {
                            BottomNavBar(navController = navController)
                        }
                    }
                ) { innerPadding ->
                    NavHost(
                        navController = navController,
                        startDestination = startDestination,
                        modifier = Modifier.padding(innerPadding)
                    ) {
                        // ==================== AUTH ====================
                        composable("login") {
                            LoginScreen(
                                navController = navController,
                                context = this@MainActivity
                            )
                        }
                        composable("register") {
                            RegisterScreen(
                                navController = navController,
                                context = this@MainActivity
                            )
                        }

                        // ==================== MAIN TABS ====================
                        composable("home") {
                            HomeScreen(navController = navController)
                        }
                        composable("search") {
                            SearchScreen(navController = navController)
                        }
                        composable("map") {
                            MapScreen(navController = navController)
                        }
                        composable("chat_list") {
                            ChatListScreen(navController = navController)
                        }
                        composable("profile") {
                            ProfileScreen(navController = navController)
                        }

                        // ==================== SECONDARY SCREENS ====================
                        composable("create_article") {
                            CreateArticleScreen(navController = navController)
                        }
                        composable("settings") {
                            SettingsScreen(navController = navController)
                        }
                        composable("notifications") {
                            NotificationsScreen(navController = navController)
                        }

                        // ==================== DETAIL SCREENS ====================
                        composable(
                            route = "article_detail/{articleId}",
                            arguments = listOf(navArgument("articleId") { type = NavType.IntType })
                        ) { backStackEntry ->
                            val articleId = backStackEntry.arguments?.getInt("articleId") ?: 0
                            ArticleDetailScreen(navController = navController, articleId = articleId)
                        }

                        composable(
                            route = "chat_detail/{chatId}",
                            arguments = listOf(navArgument("chatId") { type = NavType.IntType })
                        ) { backStackEntry ->
                            val chatId = backStackEntry.arguments?.getInt("chatId") ?: 0
                            ChatDetailScreen(navController = navController, chatId = chatId)
                        }
                    }
                }
            }
        }
    }
}
