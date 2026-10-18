package com.example.penipuandetector.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.penipuandetector.ui.screens.DashboardScreen
import com.example.penipuandetector.ui.screens.DetectScreen
import com.example.penipuandetector.ui.screens.HistoryScreen
import com.example.penipuandetector.ui.screens.ModelInfoScreen
import com.example.penipuandetector.ui.screens.ResultScreen
import com.example.penipuandetector.ui.screens.SplashScreen

object Routes {
    const val SPLASH = "splash"
    const val DASHBOARD = "dashboard"
    const val DETECT = "detect"
    const val RESULT = "result/{id}"
    const val HISTORY = "history"
    const val MODEL_INFO = "model-info"

    fun result(id: Long): String = "result/$id"
}

@Composable
fun PenipuanNavHost() {
    val navController = rememberNavController()

    NavHost(navController = navController, startDestination = Routes.SPLASH) {
        composable(Routes.SPLASH) {
            SplashScreen(
                onStart = {
                    navController.navigate(Routes.DASHBOARD) {
                        popUpTo(Routes.SPLASH) { inclusive = true }
                    }
                },
            )
        }

        composable(Routes.DASHBOARD) {
            DashboardScreen(
                onDetect = { navController.navigate(Routes.DETECT) },
                onHistory = { navController.navigate(Routes.HISTORY) },
                onModelInfo = { navController.navigate(Routes.MODEL_INFO) },
                onOpenDetection = { id -> navController.navigate(Routes.result(id)) },
            )
        }

        composable(Routes.DETECT) {
            DetectScreen(
                onBack = { navController.popBackStack() },
                onResult = { id ->
                    navController.navigate(Routes.result(id)) {
                        popUpTo(Routes.DASHBOARD)
                        launchSingleTop = true
                    }
                },
            )
        }

        composable(
            route = Routes.RESULT,
            arguments = listOf(navArgument("id") { type = NavType.LongType }),
        ) {
            ResultScreen(
                onBack = { navController.popBackStack() },
                onDetectAgain = {
                    navController.navigate(Routes.DETECT) {
                        popUpTo(Routes.DASHBOARD)
                    }
                },
                onHistory = { navController.navigate(Routes.HISTORY) },
            )
        }

        composable(Routes.HISTORY) {
            HistoryScreen(
                onBack = { navController.popBackStack() },
                onDetect = {
                    navController.navigate(Routes.DETECT) {
                        popUpTo(Routes.DASHBOARD)
                    }
                },
            )
        }

        composable(Routes.MODEL_INFO) {
            ModelInfoScreen(onBack = { navController.popBackStack() })
        }
    }
}
