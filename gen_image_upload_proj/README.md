# Supabase 이미지 업로드 프로젝트

이 프로젝트는 Supabase, Cloudflare R2 를 사용하여 이미지 데이터를 관리하는 Python 스크립트입니다.

## 설치

1. 필요한 라이브러리 설치:
```bash
pip install -r requirements.txt
```

## 환경 설정

1. `.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Supabase 설정
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

## 사용법


### 1. dotenv 테스트
```bash
python dotenv_example.py
```

### 2. supabase 테스트
```bash
python supabase_example.py
```

## 주요 기능
- ✅ 환경변수를 통한 안전한 설정 관리
- ✅ Cloudflare 이미지 업로드
- ✅ Supabase 에 메타 데이터 저장
- ✅ 배치 처리로 대량 데이터 처리

## 파일 구조

- `supabase_example.py`: supabase 예제
- `dotenv_example.py`: dotenv 사용 예시
- `requirements.txt`: 필요한 라이브러리 목록
- `.env`: 환경변수 설정 (직접 생성 필요)

## 주의사항
- Supabase 프로젝트에서 테이블을 먼저 생성해야 합니다 