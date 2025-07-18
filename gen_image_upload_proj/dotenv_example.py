import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env 파일 로드
load_dotenv()

# 환경변수에서 설정 가져오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# 설정 확인
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ 환경변수가 설정되지 않았습니다!")
    print("📋 .env 파일에 다음을 추가해주세요:")
    print("SUPABASE_URL=your_supabase_url")
    print("SUPABASE_ANON_KEY=your_supabase_anon_key")
    exit(1)

print("✅ 환경변수 로드 완료!")
print(f"URL: {SUPABASE_URL}")
print(f"Key: {SUPABASE_ANON_KEY[:20]}...")

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# 테스트 연결
try:
    # 간단한 쿼리로 연결 테스트
    response = supabase.table('images').select("id", count='exact').limit(1).execute()
    print("✅ Supabase 연결 성공!")
except Exception as e:
    print(f"❌ Supabase 연결 실패: {str(e)}")

