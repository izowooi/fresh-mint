package com.freshmint.firebase

import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.database.*
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

object FirebaseHelper {
    private lateinit var database: FirebaseDatabase
    private lateinit var reference: DatabaseReference
    private var isInitialized = false

    init {
        println("FirebaseHelper init() called isInitialized: $isInitialized")
        initFirebase()
    }

    fun initFirebase() {
        if(isInitialized) return

        database = FirebaseDatabase.getInstance("https://fresh-mint.firebaseio.com/")
        reference = database.getReference("servers")
        isInitialized = true
    }

    fun loginFirebaseAuth() {
        FirebaseAuth.getInstance().signInAnonymously()
            .addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    val user = FirebaseAuth.getInstance().currentUser
                    println("login success()-> uid : ${user?.uid}")
                } else {
                    val exception = task.exception
                    println("login failed()-> ${exception?.message}")
                }
            }
    }

    suspend fun getServerNames(): List<String> = suspendCancellableCoroutine { continuation ->
        reference.addListenerForSingleValueEvent(object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                val serverNames = snapshot.children.map { it.key ?: "" }
                continuation.resume(serverNames)
            }

            override fun onCancelled(error: DatabaseError) {
                Log.e("FirebaseHelper", "DB access cancelled/failed: ${error.message}")
                continuation.resumeWithException(error.toException())
            }
        })
    }

    suspend fun getAccessDate(serverName: String): List<String> = suspendCancellableCoroutine { continuation ->
        val serverRef = reference.child(serverName)
        serverRef.child("access_date")
            .addListenerForSingleValueEvent(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    val list = snapshot.getValue<List<String>>()
                    continuation.resume(list ?: emptyList())
                }

                override fun onCancelled(error: DatabaseError) {
                    Log.e("FirebaseHelper", "DB access cancelled/failed: ${error.message}")
                    continuation.resumeWithException(error.toException())
                }
            })
    }
}