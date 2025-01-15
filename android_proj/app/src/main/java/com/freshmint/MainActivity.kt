package com.freshmint

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.ui.tooling.preview.Preview
import com.freshmint.ui.theme.FreshMintTheme
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.freshmint.firebase.FirebaseHelper


class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FreshMintTheme {
                ServerStatusScreen()
            }
        }
    }
}

// 임의 데이터 클래스
data class ServerData(
    val status: String,           // "정상" 또는 "비정상"
    val serverName: String,       // "server1", "server2" 등
    val updatedDateTime: String   // "2025-01-13 01:30:16" 등
)

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun ServerStatusScreen() {
    // 임의의 서버 정보 목록
    val serverList = listOf(
        ServerData("정상", "server1", "2025-01-13 01:30:16"),
        ServerData("비정상", "server2", "2025-01-13 02:10:47"),
        ServerData("정상", "server3", "2025-01-13 03:00:00"),
        ServerData("비정상", "server4", "2025-01-13 03:45:12"),
    )

    // 화면 전체를 세로(Column)로 구성
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.Center
    ) {
        // 상단 4개의 Row: 서버 상태, 서버명, 갱신 날짜 표시
        serverList.forEach { server ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 상태에 따라 아이콘과 색상 변경
                val icon = if (server.status == "정상") {
                    Icons.Filled.CheckCircle
                } else {
                    Icons.Outlined.CheckCircle
                }
                val iconTint = if (server.status == "정상") {
                    Color.Green
                } else {
                    Color.Red
                }

                // 아이콘 표시
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = iconTint,
                    modifier = Modifier.size(24.dp)
                )

                Spacer(modifier = Modifier.width(8.dp))

                // 서버명
                Text(
                    text = server.serverName,
                    modifier = Modifier.weight(1f)
                )

                // 갱신 날짜
                Text(text = server.updatedDateTime)
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // 마지막 Row: refresh_1, refresh_2 버튼 2개
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Button(onClick = {
                FirebaseHelper.getAccessDate("server1") { accessDateList ->
                    println("AccessDateList: $accessDateList")
                }
            }) {
                Text(text = "refresh_1")
            }
            Button(onClick = {
                println("on click")
                FirebaseHelper.getServerNames { serverNames ->
                    for (serverName in serverNames) {
                        println("ServerName: $serverName")
                    }
                }
            }) {
                Text(text = "refresh_2")
            }
            Button(onClick = {
                FirebaseHelper.loginFirebaseAuth()
            }) {
                Text(text = "refresh_3")
            }
        }
    }
}