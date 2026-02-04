package com.example.aplicacionmovil.ui.main

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.example.aplicacionmovil.ui.theme.AplicacionMovilTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            AplicacionMovilTheme {
                val navController = rememberNavController()
                NavHost(navController = navController, startDestination = "canciones") {
                    composable("login") {
                        LoginScreen(
                            navController = navController,
                            context = this@MainActivity
                        )
                    }
                }
            }
        }
    }
}