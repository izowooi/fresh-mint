package com.freshmint.firebase

import android.util.Log
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.database.*
import com.google.firebase.ktx.Firebase
import com.google.firebase.database.ktx.database

class FirebaseHelper {

    private lateinit var database: FirebaseDatabase
    private lateinit var reference: DatabaseReference

    fun loginFirebaseAuth() {
        FirebaseAuth.getInstance().signInAnonymously()
            .addOnCompleteListener { task ->
                if (task.isSuccessful) {
                    // 인증 성공
                    val user = FirebaseAuth.getInstance().currentUser
                    println("login success()-> uid : ${user?.uid}")
                    // user.uid 등 사용 가능
                    // 이후 DB 읽기/쓰기 가능 (Rules: auth != null 일 때)
                } else {
                    // 인증 실패
                    val exception = task.exception
                    // 에러 처리
                }
            }
    }
    /**
     * Firebase Realtime DB 초기화
     * 프로젝트 세팅에서 이미 Firebase 연동이 되어 있다고 가정합니다.
     */
    fun initFirebase() {
        // getInstance()를 통해 특정 DB URL 설정
        database = FirebaseDatabase.getInstance("https://fresh-mint.firebaseio.com/")
        // 해당 경로를 참조 (servers/server_1)
        reference = database.getReference("servers").child("server1")
    }

    /**
     * access_date 키 값 (['aaa', 'bbb'] 같은 리스트) 을 가져옴
     * @param onResult: 콜백으로 리스트 결과를 전달
     */
    fun getAccessDate(onResult: (List<String>) -> Unit) {
        var dbref = reference.child("access_date")
            .addListenerForSingleValueEvent(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    // Realtime DB에서 가져온 값을 List<String> 형태로 변환
                    val list = snapshot.getValue<List<String>>()
                    // 결과 콜백
                    onResult(list ?: emptyList())
                }

                override fun onCancelled(error: DatabaseError) {
                    // 에러 처리
                    Log.e("FirebaseHelper", "DB access cancelled/failed: ${error.message}")
                    onResult(emptyList())
                }
            })
    }
}