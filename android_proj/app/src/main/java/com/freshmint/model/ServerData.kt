package com.freshmint.model

data class ServerData(
    val status: String,           // "정상" 또는 "비정상"
    val serverName: String,       // "server1", "server2" 등
    val updatedDateTime: String   // "2025-01-13 01:30:16" 등
)
