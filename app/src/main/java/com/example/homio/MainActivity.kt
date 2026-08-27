package com.example.homio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.homio.theme.*
import com.example.homio.ui.HomioViewModel
import com.example.homio.ui.components.ReosTopBar
import com.example.homio.ui.screens.*

class MainActivity : ComponentActivity() {
    private val viewModel: HomioViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            HomioTheme {
                MainAppScreen(viewModel = viewModel)
            }
        }
    }
}

data class NavItem(
    val title: String,
    val selectedIcon: ImageVector,
    val unselectedIcon: ImageVector,
    val testTag: String
)

@Composable
fun MainAppScreen(viewModel: HomioViewModel) {
    val selectedTab by viewModel.selectedTab.collectAsState()
    val operatingMode by viewModel.operatingMode.collectAsState()
    val userNotification by viewModel.userNotification.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(userNotification) {
        userNotification?.let {
            snackbarHostState.showSnackbar(it, duration = SnackbarDuration.Short)
            viewModel.dismissNotification()
        }
    }

    val navItems = listOf(
        NavItem("Overview", Icons.Filled.Dashboard, Icons.Outlined.Dashboard, "nav_overview"),
        NavItem("Gates", Icons.Filled.Layers, Icons.Outlined.Layers, "nav_gates"),
        NavItem("Leads", Icons.Filled.PersonSearch, Icons.Outlined.PersonSearch, "nav_leads"),
        NavItem("Deals", Icons.Filled.MonetizationOn, Icons.Outlined.MonetizationOn, "nav_deals"),
        NavItem("Security", Icons.Filled.Security, Icons.Outlined.Security, "nav_security")
    )

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            ReosTopBar(
                operatingMode = operatingMode,
                onSnapshotClick = { viewModel.createSnapshot() },
                onVerifyClick = { viewModel.runPreflightIntegrityCheck() }
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = SurfaceNavy,
                tonalElevation = 8.dp,
                windowInsets = WindowInsets.navigationBars
            ) {
                navItems.forEachIndexed { index, item ->
                    val isSelected = selectedTab == index
                    NavigationBarItem(
                        selected = isSelected,
                        onClick = { viewModel.selectTab(index) },
                        icon = {
                            Icon(
                                imageVector = if (isSelected) item.selectedIcon else item.unselectedIcon,
                                contentDescription = item.title
                            )
                        },
                        label = {
                            Text(
                                text = item.title,
                                style = MaterialTheme.typography.labelSmall,
                                fontSize = 10.sp
                            )
                        },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = DarkNavy,
                            selectedTextColor = CyanAccent,
                            indicatorColor = CyanAccent,
                            unselectedIconColor = TextSecondary,
                            unselectedTextColor = TextSecondary
                        )
                    )
                }
            }
        },
        containerColor = DarkNavy,
        contentWindowInsets = WindowInsets(0, 0, 0, 0)
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .background(DarkNavy)
        ) {
            when (selectedTab) {
                0 -> DashboardScreen(
                    viewModel = viewModel,
                    onNavigateToGates = { viewModel.selectTab(1) },
                    onNavigateToLeads = { viewModel.selectTab(2) },
                    onNavigateToDeals = { viewModel.selectTab(3) },
                    onNavigateToSecurity = { viewModel.selectTab(4) }
                )
                1 -> ArchitectureGatesScreen(viewModel = viewModel)
                2 -> LeadEngineScreen(viewModel = viewModel)
                3 -> InventoryDealsScreen(viewModel = viewModel)
                4 -> EvidenceSecurityScreen(viewModel = viewModel)
            }
        }
    }
}
