from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import random
from datetime import datetime
import os
from supabase import create_client, Client
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Image Gallery API",
    description="Cloud Run에서 실행되는 이미지 갤러리 API with Supabase",
    version="2.0.0"
)

# CORS 설정 (모든 오리진 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase 클라이언트 초기화
supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """Supabase 클라이언트를 가져오거나 생성"""
    global supabase_client

    if supabase_client is None:
        # 환경변수에서 가져오기 (Cloud Run은 환경변수 사용)
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

        if not SUPABASE_URL or not SUPABASE_KEY:
            logger.warning("Supabase 환경변수가 설정되지 않았습니다. DB 기능이 비활성화됩니다.")
            return None

        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Supabase 클라이언트 초기화 성공")
        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {str(e)}")
            return None

    return supabase_client


# R2 이미지 URL (폴백용)
R2_IMAGE_URL = "https://pub-faf21c880e254e7483b84cb14bb8854e.r2.dev/Firefly_ff-00198%20Steady%20portrait%20of%20a%20be%20168550%20uqj.jpg"


@app.on_event("startup")
async def startup_event():
    """앱 시작시 Supabase 연결 테스트"""
    client = get_supabase_client()
    if client:
        try:
            # 연결 테스트
            response = client.table('images').select("id").limit(1).execute()
            logger.info("Supabase 연결 테스트 성공")
        except Exception as e:
            logger.error(f"Supabase 연결 테스트 실패: {str(e)}")


@app.get("/ping")
async def ping():
    """헬스체크 및 연결 테스트용 엔드포인트"""
    supabase_status = "connected" if get_supabase_client() else "disconnected"

    return {
        "status": "healthy",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cloud-run-fastapi",
        "region": os.environ.get("REGION", "unknown"),
        "revision": os.environ.get("K_REVISION", "unknown"),
        "supabase_status": supabase_status
    }


@app.get("/random-images")
async def get_random_images(
        count: int = Query(10, ge=1, le=50, description="반환할 이미지 개수"),
        use_db: bool = Query(True, description="DB 사용 여부")
) -> Dict:
    """랜덤하게 이미지 URL을 반환하는 엔드포인트"""

    # DB 사용 시도
    if use_db:
        client = get_supabase_client()
        if client:
            try:
                db_images = await get_random_images_from_db(client, count)
                if db_images:
                    return {
                        "count": len(db_images),
                        "images": db_images,
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "supabase"
                    }
            except Exception as e:
                logger.error(f"DB에서 이미지 가져오기 실패: {str(e)}")

    # DB를 사용할 수 없거나 실패한 경우 폴백
    return await get_fallback_images(count)


async def get_random_images_from_db(client: Client, count: int) -> List[Dict]:
    """Supabase DB에서 랜덤 이미지 가져오기"""
    try:
        # 전체 이미지 개수 확인
        count_response = client.table('images').select("*", count='exact').execute()
        total_count = count_response.count if hasattr(count_response, 'count') else 0

        if total_count == 0:
            logger.warning("DB에 이미지가 없습니다.")
            return []

        logger.info(f"총 {total_count}개의 이미지가 DB에 있습니다.")

        # 요청 개수 조정
        actual_count = min(count, total_count)

        # 랜덤 오프셋 사용 (큰 DB)
        selected_images = []
        used_offsets = set()

        for _ in range(actual_count):
            attempts = 0
            while attempts < 10:
                offset = random.randint(0, total_count - 1)
                if offset not in used_offsets:
                    used_offsets.add(offset)
                    response = client.table('images') \
                        .select("id, url, title, tags, tag_prefix, metadata, created_at") \
                        .limit(1) \
                        .offset(offset) \
                        .execute()

                    if response.data:
                        selected_images.extend(response.data)
                        break
                attempts += 1

        # 응답 형식 맞추기
        formatted_images = []
        for img in selected_images:
            formatted_images.append({
                "id": img.get('id', f"img_{random.randint(10000, 99999)}"),
                "url": img.get('url', R2_IMAGE_URL),
                "title": img.get('title', 'Untitled Image'),
                "description": f"Image from database with tags: {', '.join(img.get('tags', [])[:3])}",
                "metadata": img.get('metadata', {
                    "width": 300,
                    "height": 300,
                    "format": "jpg"
                }),
                "tags": img.get('tags', []),
                "tag_prefix": img.get('tag_prefix', 'IMG'),
                "created_at": img.get('created_at', datetime.utcnow().isoformat())
            })

        logger.info(f"DB에서 {len(formatted_images)}개 이미지 조회 성공")
        return formatted_images

    except Exception as e:
        logger.error(f"DB 조회 중 오류: {str(e)}")
        raise


async def get_fallback_images(count: int) -> Dict:
    """DB를 사용할 수 없을 때 폴백 이미지 반환"""
    images = []

    for i in range(count):
        img_id = random.randint(10000, 99999)

        images.append({
            "id": f"img_{img_id}",
            "url": R2_IMAGE_URL,
            "title": f"Fallback Image {img_id}",
            "description": f"This is a fallback image with ID {img_id}",
            "metadata": {
                "width": 300,
                "height": 300,
                "format": "jpg",
                "size_kb": random.randint(50, 150)
            },
            "tags": random.sample(["portrait", "artistic", "firefly", "steady", "beautiful"], k=3),
            "tag_prefix": "FALLBACK",
            "created_at": datetime.utcnow().isoformat()
        })

    return {
        "count": count,
        "images": images,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "fallback"
    }


@app.get("/images/stats")
async def get_image_stats():
    """DB 이미지 통계 반환"""
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # 전체 개수
        count_response = client.table('images').select("*", count='exact').execute()
        total_count = count_response.count if hasattr(count_response, 'count') else 0

        # 태그별 통계 (샘플)
        sample_response = client.table('images').select("tags").limit(100).execute()
        tag_counts = {}

        if sample_response.data:
            for img in sample_response.data:
                for tag in img.get('tags', []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_images": total_count,
            "top_tags": dict(top_tags),
            "database": "supabase",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """API 정보를 반환하는 루트 엔드포인트"""
    supabase_enabled = get_supabase_client() is not None

    return {
        "message": "Image Gallery API on Google Cloud Run",
        "version": "2.0.0",
        "endpoints": {
            "ping": "/ping - 헬스체크",
            "random_images": "/random-images?count=10&use_db=true - 랜덤 이미지 반환",
            "image_stats": "/images/stats - DB 이미지 통계",
            "docs": "/docs - API 문서 (Swagger UI)",
            "redoc": "/redoc - API 문서 (ReDoc)"
        },
        "features": {
            "database": "Supabase" if supabase_enabled else "Disabled",
            "fallback": "Available"
        },
        "deployment": {
            "platform": "Google Cloud Run",
            "region": os.environ.get("REGION", "unknown"),
            "service": os.environ.get("K_SERVICE", "unknown")
        }
    }


# Cloud Run은 PORT 환경변수를 자동으로 설정함
if __name__ == "__main__":
    import uvicorn

    # 로컬 개발시 .env 파일 로드 (선택사항)
    try:
        from dotenv import load_dotenv

        load_dotenv()
        logger.info("로컬 환경: .env 파일 로드됨")
    except ImportError:
        logger.info("프로덕션 환경: 환경변수 사용")

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)