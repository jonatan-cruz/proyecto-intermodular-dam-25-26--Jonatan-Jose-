package com.example.aplicacionmovil.ui.main

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.aplicacionmovil.ui.products.create.CreateArticleScreen
import com.example.aplicacionmovil.ui.theme.AplicacionMovilTheme
import com.example.aplicacionmovil.ui.products.detail.ArticleDetailScreen
import androidx.navigation.NavType
import androidx.navigation.navArgument

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AplicacionMovilTheme {
                val navController = rememberNavController()
                val sessionManager = remember { com.example.aplicacionmovil.data.local.SessionManager(this@MainActivity) }
                val startDestination = if (sessionManager.fetchAuthToken() != null) "home" else "login"

                Scaffold(modifier = Modifier.Companion.fillMaxSize()) { innerPadding ->
                    NavHost(
                        navController = navController,
                        startDestination = startDestination,
                        modifier = Modifier.Companion.padding(innerPadding)
                    ) {
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
                        composable("home") {
                            HomeScreen(navController = navController)
                        }
                        composable ("create_article"){
                            CrearArticulo(navController=navController)
                        }
                        composable("settings") {
                            SettingsScreen(navController = navController)
                        }
                        composable("profile") {
                            ProfileScreen(navController = navController)
                        }
                        composable("notifications") {
                            NotificationsScreen(navController = navController)
                        }
                        composable("search") {
                            SearchScreen(navController = navController)
                        }
                        composable(
                            route = "article_detail/{articleId}",
                            arguments = listOf(navArgument("articleId") { type = NavType.IntType })
                        ) { backStackEntry ->
                            val articleId = backStackEntry.arguments?.getInt("articleId") ?: 0
                            ArticleDetailScreen(navController = navController, articleId = articleId)
                        }
                        // Aquí puedes añadir más rutas para otras pantallas
                        // composable("home") { HomeScreen(...) }
                        // composable("register") { RegisterScreen(...) }
                    }
                }
            }
        }
    }
}