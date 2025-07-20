# Google Cloud Run 배포 가이드

## 📖 참고 문서
- [Python 서비스 빌드 및 배포 가이드](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service?hl=ko)

## 🚀 배포 준비

### 1. gcloud CLI 설정
```bash
# gcloud CLI 설치 확인
which gcloud

# Google Cloud 인증
gcloud auth login

# 프로젝트 초기화
gcloud init

# 프로젝트 설정
gcloud config set project fresh-mint-63c38

# 필요한 서비스 활성화
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### 2. 환경 변수 설정
Cloud Run 서비스에서 다음 환경 변수를 설정해야 합니다:

| 변수명 | 설명 |
|--------|------|
| `SUPABASE_URL` | Supabase 프로젝트 URL |
| `SUPABASE_ANON_KEY` | Supabase 익명 키 |

#### 환경 변수 설정 방법
1. [Cloud Run Console](https://console.cloud.google.com/run) 접속
2. `image-gallery-api` 서비스 클릭
3. 상단의 **"EDIT & DEPLOY NEW REVISION"** 클릭
4. **Container** 탭 → **Variables & Secrets** 섹션에서 환경 변수 추가

## 🔧 배포 실행

```bash
# 배포 스크립트 실행 권한 부여 및 실행
chmod +x ./deploy.sh && ./deploy.sh

# 또는 직접 실행
./deploy.sh
```

## 📁 프로젝트 구조
```
cloudrun_proj/
├── deploy.sh          # 배포 스크립트
├── Dockerfile         # Docker 이미지 빌드 설정
├── main.py           # 메인 애플리케이션
├── requirements.txt  # Python 의존성
└── README.md        # 이 문서
```