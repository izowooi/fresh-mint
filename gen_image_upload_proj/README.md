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

# Cloudflare R2 설정
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_ACCOUNT_ID=your_account_id
R2_BUCKET=your_bucket_name
R2_PUBLIC_URL=https://your-bucket.r2.dev

# 기타 설정 (선택사항)
SAMPLE_COUNT=1
BATCH_SIZE=50
```

## 사용법


### 1. 메인 플로우 실행 (권장)
```bash
# 기본 폴더 ./images 사용
python main_flow.py

# 특정 폴더 지정
python main_flow.py --folder /path/to/images

# R2 경로와 배치 크기 지정
python main_flow.py --folder ./photos --r2-prefix 2024/01 --batch-size 20

# 대화형 모드
python main_flow.py --interactive

# 도움말 보기
python main_flow.py --help
```

### 2. 개별 모듈 테스트
```bash
# Supabase 연결 테스트
python dotenv_example.py

# Supabase 데이터 삽입 테스트
python supabase_example.py

# R2 업로드 테스트
python cloudflare_r2_example.py
```

## 주요 기능
- ✅ 환경변수를 통한 안전한 설정 관리
- ✅ Cloudflare 이미지 업로드
- ✅ Supabase 에 메타 데이터 저장
- ✅ 배치 처리로 대량 데이터 처리

## 파일 구조

### 메인 스크립트
- `main_flow.py`: **메인 플로우** - 이미지 업로드 및 DB 저장
- `r2_uploader.py`: Cloudflare R2 업로드 모듈
- `supabase_manager.py`: Supabase DB 관리 모듈

### 예시 및 테스트
- `supabase_example.py`: Supabase 테스트 스크립트
- `cloudflare_r2_example.py`: R2 업로드 테스트 스크립트
- `dotenv_example.py`: dotenv 사용 예시

### 설정 파일
- `requirements.txt`: 필요한 라이브러리 목록
- `.env`: 환경변수 설정 (직접 생성 필요)

## 주의사항
- Supabase 프로젝트에서 테이블을 먼저 생성해야 합니다 