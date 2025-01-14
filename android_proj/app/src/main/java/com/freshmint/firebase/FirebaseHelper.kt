package com.freshmint.firebase

import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.database.*

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


    fun getServerNames(onResult: (List<String>) -> Unit) {
        reference.addListenerForSingleValueEvent(object : ValueEventListener {
            override fun onDataChange(snapshot: DataSnapshot) {
                val serverNames = snapshot.children.map { it.key ?: "" }
                onResult(serverNames)
            }

            override fun onCancelled(error: DatabaseError) {
                Log.e("FirebaseHelper", "DB access cancelled/failed: ${error.message}")
                onResult(emptyList())
            }
        })
    }

    fun getAccessDate(serverName: String, onResult: (List<String>) -> Unit) {
        var serverRef = reference.child(serverName)
        var dbref = serverRef.child("access_date")
            .addListenerForSingleValueEvent(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    val list = snapshot.getValue<List<String>>()
                    onResult(list ?: emptyList())
                }

                override fun onCancelled(error: DatabaseError) {
                    Log.e("FirebaseHelper", "DB access cancelled/failed: ${error.message}")
                    onResult(emptyList())
                }
            })
    }
}