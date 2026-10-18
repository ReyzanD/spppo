package com.example.penipuandetector

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.example.penipuandetector.ui.navigation.PenipuanNavHost
import com.example.penipuandetector.ui.theme.PenipuanTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            PenipuanTheme {
                PenipuanNavHost()
            }
        }
    }
}
