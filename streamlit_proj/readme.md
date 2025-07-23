# 🖼️ 이미지 갤러리 앱

Streamlit을 사용하여 구축된 반응형 이미지 갤러리 웹 애플리케이션입니다. Cloud Run에서 호스팅되는 API를 통해 이미지를 동적으로 로드하고 표시합니다.

## ✨ 주요 기능

- **그리드 레이아웃**: 4열 그리드로 이미지를 깔끔하게 표시
- **무한 스크롤**: "더 많은 이미지 보기" 버튼으로 추가 이미지 로드
- **상세 메타데이터**: 각 이미지의 크기, 포맷, 파일 크기, 프롬프트 등 상세 정보 제공
- **WebP 최적화**: 최적화된 WebP 이미지 포맷 지원
- **로딩 애니메이션**: 이미지 로딩 중 shimmer 효과
- **호버 효과**: 이미지에 마우스를 올리면 부드러운 애니메이션 효과
- **API 상태 모니터링**: 실시간 API 연결 상태 확인

## 🛠️ 기술 스택

- **Frontend**: Streamlit
- **이미지 저장소**: Cloudflare R2
- **백엔드 API**: Google Cloud Run
- **데이터베이스**: Supabase

## 🚀 설치 및 실행

### 1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 애플리케이션 실행
```bash
streamlit run gallery_app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 갤러리를 확인할 수 있습니다.

## 🌐 API 정보

### 엔드포인트
- **이미지 API**: `https://image-gallery-api-513122275637.asia-northeast3.run.app/random-images`
- **상태 확인**: `https://image-gallery-api-513122275637.asia-northeast3.run.app/ping`

### API 응답 구조
```json
{
  "count": 10,
  "images": [
    {
      "id": "img_unique_id",
      "url": "https://pub-example.r2.dev/webp/image.webp",
      "title": "이미지 제목",
      "description": "이미지 설명",
      "metadata": {
        "width": 2304,
        "height": 1792,
        "format": "jpeg",
        "size_kb": 95.35,
        "webp_url": "WebP 이미지 URL",
        "content_type": "image/webp",
        "has_original": false,
        "original_url": null
      },
      "tags": ["태그1", "태그2", "태그3"],
      "tag_prefix": "FF-00104",
      "created_at": "2025-07-20T13:02:10.139162+00:00"
    }
  ],
  "timestamp": "2025-07-20T15:16:08.200583",
  "source": "supabase"
}
```

## 📱 사용법

1. **갤러리 보기**: 페이지 로드 시 자동으로 20개의 이미지가 표시됩니다
2. **상세 정보 확인**: 각 이미지 카드의 "상세 정보" 확장 메뉴 클릭
3. **갤러리 초기화**: 사이드바의 "갤러리 초기화" 버튼으로 새로고침
4. **API 상태 확인**: 사이드바의 "API 상태 확인" 버튼으로 연결 상태 모니터링

## 📁 프로젝트 구조

```
streamlit_proj/
├── gallery_app.py      # 메인 Streamlit 애플리케이션
├── requirements.txt    # Python 의존성
├── readme.md          # 프로젝트 문서
└── venv/              # 가상환경 (gitignore)
```

## 🎨 주요 기능 상세

### 이미지 카드
- **제목**: 원본 파일명 기반
- **설명**: AI 생성 이미지 설명
- **메타데이터**: 해상도, 파일 크기, 포맷 정보
- **태그**: 이미지 관련 키워드
- **생성 날짜**: 이미지 업로드 시간
- **WebP 최적화**: 빠른 로딩을 위한 최적화된 이미지 포맷

### 인터페이스
- **반응형 디자인**: 다양한 화면 크기에 최적화
- **로딩 애니메이션**: 이미지 로드 중 shimmer 효과
- **호버 효과**: 마우스 오버 시 이미지 확대 효과
- **정보 버튼**: 이미지 우하단 ℹ️ 버튼으로 태그 정보 확인

## 🔧 설정

애플리케이션의 주요 설정값들:

- **이미지 로드 개수**: 한 번에 20개씩 로드
- **그리드 열 수**: 4열 고정 레이아웃
- **API 타임아웃**: 30초 (콜드 스타트 고려)
- **로딩 지연**: 0.1초 (로딩 효과 표시용)

**Powered by** Cloud Run + Cloudflare R2 + Supabase
