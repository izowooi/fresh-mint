import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone
import random
import uuid
from typing import List, Dict
import time
import json

# .env 파일 로드
load_dotenv()

# Supabase 클라이언트 설정
# 환경변수에서 가져오기
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

# 설정 확인
if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ 환경변수가 설정되지 않았습니다!")
    print("📋 .env 파일에 다음을 추가해주세요:")
    print("SUPABASE_URL=your_supabase_url")
    print("SUPABASE_ANON_KEY=your_supabase_anon_key")
    exit(1)

# Supabase 클라이언트 생성
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 테이블 생성 SQL (Supabase SQL Editor에서 실행)
CREATE_TABLE_SQL = """
-- 이미지 테이블 생성
CREATE TABLE IF NOT EXISTS images (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    tags TEXT[],
    tag_prefix TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_images_tags ON images USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_images_tag_prefix ON images(tag_prefix);
"""


# 샘플 데이터 생성 함수
def generate_sample_data(count: int = 100) -> List[Dict]:
    """샘플 이미지 데이터 생성"""

    # 샘플 태그 목록
    tag_categories = {
        "style": ["portrait", "landscape", "abstract", "minimalist", "vintage", "modern"],
        "color": ["vibrant", "monochrome", "pastel", "dark", "bright", "colorful"],
        "mood": ["peaceful", "energetic", "mysterious", "romantic", "dramatic", "serene"],
        "subject": ["nature", "urban", "people", "animals", "architecture", "food"]
    }

    # 태그 접두어 목록
    tag_prefixes = ["FD-00001", "FD-00002", "FD-00003", "FD-00004", "FD-00005"]

    # R2 URL 템플릿
    r2_base_url = "https://genimage.zowoo.uk"

    sample_data = []

    for i in range(count):
        # 고유 ID 생성
        image_id = f"img_{uuid.uuid4().hex[:8]}"

        # 랜덤 태그 선택 (각 카테고리에서 1개씩)
        tags = []
        for category, options in tag_categories.items():
            tags.append(random.choice(options))

        # 추가 랜덤 태그
        tags.extend(random.sample(sum(tag_categories.values(), []), k=random.randint(1, 3)))
        tags = list(set(tags))  # 중복 제거

        # 메타데이터 생성 (None 값 제거, 구조 단순화)
        metadata = {
            "width": random.choice([300, 600, 800, 1024, 1920]),
            "height": random.choice([300, 400, 600, 768, 1080]),
            "format": random.choice(["jpg", "png", "webp"]),
            "size_kb": random.randint(50, 500),
            "quality": random.choice(["standard", "high", "ultra"]),
        }

        # 이미지 데이터 생성
        image_data = {
            "id": image_id,
            "url": f"{r2_base_url}/sample_image_{i:05d}.jpg",
            "title": f"Sample Image {i:05d} - {random.choice(tags).title()}",
            "tags": tags,
            "tag_prefix": random.choice(tag_prefixes),
            "metadata": metadata
            # created_at은 DB에서 자동 생성
        }

        sample_data.append(image_data)

    return sample_data


def validate_image_data(image_data: Dict) -> bool:
    """이미지 데이터 유효성 검사"""
    try:
        # JSON 직렬화 테스트
        json.dumps(image_data)
        
        # 필수 필드 확인
        required_fields = ['id', 'url', 'title', 'tags', 'tag_prefix', 'metadata']
        for field in required_fields:
            if field not in image_data:
                print(f"❌ 필수 필드 누락: {field}")
                return False
        
        # None 값 확인
        for key, value in image_data.items():
            if value is None:
                print(f"❌ None 값 발견: {key}")
                return False
        
        print(f"✅ 데이터 유효성 검사 통과: {image_data['id']}")
        return True
    except Exception as e:
        print(f"❌ 데이터 유효성 검사 실패: {str(e)}")
        return False


def insert_single_image(image_data: Dict) -> Dict:
    """단일 이미지 삽입"""
    try:
        # 데이터 유효성 검사
        if not validate_image_data(image_data):
            return None
            
        response = supabase.table('images').insert(image_data).execute()
        print(f"✅ 삽입 성공: {image_data['id']}")
        return response.data
    except Exception as e:
        print(f"❌ 삽입 실패: {image_data['id']} - {str(e)}")
        return None


def bulk_insert_images(images_data: List[Dict], batch_size: int = 50) -> int:
    """대량 이미지 삽입 (배치 처리)"""
    total_inserted = 0
    failed_count = 0

    # 배치로 나누어 처리
    for i in range(0, len(images_data), batch_size):
        batch = images_data[i:i + batch_size]

        try:
            response = supabase.table('images').insert(batch).execute()
            total_inserted += len(response.data)
            print(f"✅ 배치 {i // batch_size + 1} 삽입 성공: {len(response.data)}개")
        except Exception as e:
            failed_count += len(batch)
            print(f"❌ 배치 {i // batch_size + 1} 삽입 실패: {str(e)}")

            # 실패한 배치는 개별 삽입 시도
            print("개별 삽입 시도 중...")
            for image in batch:
                if insert_single_image(image):
                    total_inserted += 1
                    failed_count -= 1

        # API 제한 방지를 위한 딜레이
        time.sleep(0.5)

    return total_inserted, failed_count


def get_table_stats():
    """테이블 통계 조회"""
    try:
        # 전체 개수
        count_response = supabase.table('images').select("*", count='exact').execute()
        total_count = count_response.count

        # 태그별 통계
        all_images = supabase.table('images').select("tags").execute()
        tag_counts = {}

        for img in all_images.data:
            for tag in img.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 가장 많이 사용된 태그 상위 10개
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_images": total_count,
            "top_tags": top_tags
        }
    except Exception as e:
        print(f"통계 조회 실패: {str(e)}")
        return None


def get_random_images(count: int = 10) -> List[Dict]:
    """
    DB에서 랜덤하게 이미지를 가져오는 함수
    
    Args:
        count: 가져올 이미지 개수 (기본값: 10)
    
    Returns:
        랜덤 이미지 리스트
    """
    try:
        print(f"🎲 랜덤 이미지 {count}개 조회 중...")
        
        # 전체 이미지 개수 확인
        count_response = supabase.table('images').select("*", count='exact').execute()
        total_count = count_response.count
        
        if total_count == 0:
            print("❌ DB에 이미지가 없습니다.")
            return []
        
        print(f"📊 총 {total_count}개의 이미지가 DB에 있습니다.")
        
        # 요청 개수가 전체보다 많으면 전체 개수로 조정
        actual_count = min(count, total_count)
        
        # PostgreSQL의 TABLESAMPLE을 사용한 랜덤 조회 (대용량 DB에 효율적)
        # 하지만 Supabase에서는 제한이 있을 수 있으므로 대안 방법 사용
        
        # 방법 1: ORDER BY RANDOM() 사용 (소규모 DB에 적합)
        response = supabase.table('images')\
            .select("id, url, title, tags, tag_prefix, metadata, created_at")\
            .order("id", foreign_table=None)\
            .limit(actual_count * 3)\
            .execute()  # 여유분 조회
        
        if not response.data:
            print("❌ 이미지 조회 실패")
            return []
        
        # Python에서 랜덤 샘플링
        available_images = response.data
        if len(available_images) <= actual_count:
            selected_images = available_images
        else:
            selected_images = random.sample(available_images, actual_count)
        
        print(f"✅ 랜덤 이미지 {len(selected_images)}개 조회 완료")
        
        # 결과 출력
        print("\n📋 조회된 이미지 목록:")
        for i, img in enumerate(selected_images, 1):
            print(f"  {i}. [{img['tag_prefix']}] {img['title']}")
            print(f"     URL: {img['url']}")
            print(f"     태그: {', '.join(img['tags'][:3])}{'...' if len(img['tags']) > 3 else ''}")
            print(f"     생성일: {img['created_at']}")
            print()
        
        return selected_images
        
    except Exception as e:
        print(f"❌ 랜덤 이미지 조회 실패: {str(e)}")
        return []


def get_random_images_by_tag_prefix(tag_prefix: str, count: int = 5) -> List[Dict]:
    """
    특정 태그 접두어로 랜덤 이미지 조회
    
    Args:
        tag_prefix: 태그 접두어 (예: "FF-00220")
        count: 가져올 개수
    
    Returns:
        해당 접두어의 랜덤 이미지 리스트
    """
    try:
        print(f"🎯 태그 접두어 '{tag_prefix}'로 랜덤 이미지 {count}개 조회 중...")
        
        # 해당 태그 접두어로 검색
        response = supabase.table('images')\
            .select("id, url, title, tags, tag_prefix, metadata, created_at")\
            .eq("tag_prefix", tag_prefix.upper())\
            .execute()
        
        if not response.data:
            print(f"❌ '{tag_prefix}' 접두어를 가진 이미지가 없습니다.")
            return []
        
        available_images = response.data
        actual_count = min(count, len(available_images))
        
        # 랜덤 샘플링
        if len(available_images) <= actual_count:
            selected_images = available_images
        else:
            selected_images = random.sample(available_images, actual_count)
        
        print(f"✅ '{tag_prefix}' 이미지 {len(selected_images)}개 조회 완료")
        
        return selected_images
        
    except Exception as e:
        print(f"❌ 태그 접두어별 조회 실패: {str(e)}")
        return []


def search_images_by_tags(search_tags: List[str], limit: int = 10) -> List[Dict]:
    """
    태그로 이미지 검색
    
    Args:
        search_tags: 검색할 태그 리스트
        limit: 결과 제한
    
    Returns:
        검색된 이미지 리스트
    """
    try:
        print(f"🔍 태그 검색: {', '.join(search_tags)}")
        
        # PostgreSQL의 배열 연산자 사용 (태그가 포함된 이미지 검색)
        # @> 연산자: 좌측 배열이 우측 배열의 모든 요소를 포함하는지 확인
        response = supabase.table('images')\
            .select("id, url, title, tags, tag_prefix, metadata, created_at")\
            .contains("tags", search_tags)\
            .limit(limit)\
            .execute()
        
        if not response.data:
            print(f"❌ 태그 '{', '.join(search_tags)}'를 포함한 이미지가 없습니다.")
            return []
        
        print(f"✅ {len(response.data)}개의 이미지를 찾았습니다.")
        
        # 결과 출력
        for i, img in enumerate(response.data, 1):
            matching_tags = [tag for tag in img['tags'] if tag in search_tags]
            print(f"  {i}. [{img['tag_prefix']}] {img['title']}")
            print(f"     일치하는 태그: {', '.join(matching_tags)}")
            print()
        
        return response.data
        
    except Exception as e:
        print(f"❌ 태그 검색 실패: {str(e)}")
        return []


def main():
    """메인 실행 함수"""
    print("🚀 Supabase 이미지 DB 초기화 시작")
    print(f"URL: {SUPABASE_URL}")
    print("-" * 50)

    # 1. 테이블 생성 안내
    print("\n📋 먼저 Supabase Dashboard에서 SQL Editor를 열고")
    print("다음 SQL을 실행해주세요:\n")
    print(CREATE_TABLE_SQL)
    print("\n테이블을 생성하셨나요? (y/n): ", end="")

    if input().lower() != 'y':
        print("테이블을 먼저 생성해주세요!")
        return

    # 2. 샘플 데이터 생성
    print("\n📝 샘플 데이터 생성 중...")
    sample_count = 1  # 원하는 개수로 변경
    sample_images = generate_sample_data(sample_count)
    print(f"✅ {len(sample_images)}개의 샘플 데이터 생성 완료")

    # 3. 첫 번째 데이터 미리보기
    print("\n👀 첫 번째 데이터 미리보기:")
    print(f"ID: {sample_images[0]['id']}")
    print(f"URL: {sample_images[0]['url']}")
    print(f"Title: {sample_images[0]['title']}")
    print(f"Tags: {sample_images[0]['tags']}")
    print(f"Tag Prefix: {sample_images[0]['tag_prefix']}")
    print(f"Metadata: {sample_images[0]['metadata']}")

    # 4. 데이터 삽입
    print("\n💾 데이터베이스에 삽입을 시작하시겠습니까? (y/n): ", end="")
    if input().lower() != 'y':
        print("삽입 취소됨")
        return

    print("\n📤 데이터 삽입 중...")
    inserted, failed = bulk_insert_images(sample_images)

    print("\n✨ 삽입 완료!")
    print(f"성공: {inserted}개")
    print(f"실패: {failed}개")

    # 5. 통계 표시
    print("\n📊 데이터베이스 통계:")
    stats = get_table_stats()
    if stats:
        print(f"총 이미지 수: {stats['total_images']}개")
        print("\n🏷️ 인기 태그 TOP 10:")
        for tag, count in stats['top_tags']:
            print(f"  - {tag}: {count}개")


# 개별 이미지 삽입 예시
def insert_custom_image_example():
    """커스텀 이미지 삽입 예시"""
    custom_image = {
        "id": f"custom_{uuid.uuid4().hex[:8]}",
        "url": "https://genimage.zowoo.uk/my_special_image.jpg",
        "title": "My Special Image",
        "tags": ["special", "custom", "featured"],
        "tag_prefix": "CUSTOM",
        "metadata": {
            "width": 1920,
            "height": 1080,
            "format": "jpg",
            "size_kb": 256,
            "author": "Me",
            "copyright": "2024",
            "enhanced": True,
            "filters": ["sharpen", "color-correct"]
        }
    }

    result = insert_single_image(custom_image)
    if result:
        print("커스텀 이미지 삽입 성공!")
        print(result)


def run_sample_queries():
    """샘플 쿼리 실행 예시"""
    print("\n" + "=" * 60)
    print("🔍 샘플 쿼리 예시들")
    print("=" * 60)
    
    while True:
        print("\n📌 쿼리 메뉴:")
        print("1. 랜덤 이미지 10개 조회")
        print("2. 특정 태그 접두어로 조회")
        print("3. 태그로 검색")
        print("4. 통계 조회")
        print("5. 종료")
        
        choice = input("\n선택 (1-5): ").strip()
        
        if choice == "1":
            # 랜덤 이미지 조회
            count = input("조회할 개수 (기본값: 10): ").strip()
            count = int(count) if count.isdigit() else 10
            get_random_images(count)
            
        elif choice == "2":
            # 태그 접두어로 조회
            prefix = input("태그 접두어 입력 (예: FF-00220): ").strip().upper()
            if prefix:
                get_random_images_by_tag_prefix(prefix)
            else:
                print("❌ 태그 접두어를 입력해주세요.")
                
        elif choice == "3":
            # 태그 검색
            tags_input = input("검색할 태그들 (쉼표로 구분): ").strip()
            if tags_input:
                search_tags = [tag.strip() for tag in tags_input.split(',')]
                search_images_by_tags(search_tags)
            else:
                print("❌ 검색할 태그를 입력해주세요.")
                
        elif choice == "4":
            # 통계 조회
            stats = get_table_stats()
            if stats:
                print(f"\n📊 DB 통계:")
                print(f"  - 총 이미지: {stats['total_images']}개")
                print(f"  - 인기 태그 TOP 10:")
                for tag, count in stats['top_tags']:
                    print(f"    • {tag}: {count}개")
                    
        elif choice == "5":
            print("👋 종료합니다.")
            break
            
        else:
            print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    print("🎯 Supabase 이미지 DB 예시 스크립트")
    print("=" * 60)
    
    # 메뉴 선택
    print("\n📌 실행 메뉴:")
    print("1. 샘플 데이터 생성 및 삽입")
    print("2. 샘플 쿼리 실행")
    print("3. 커스텀 이미지 삽입")
    
    choice = input("\n선택 (1-3): ").strip()
    
    if choice == "1":
        # 기존 메인 함수 실행
        main()
    elif choice == "2":
        # 샘플 쿼리 실행
        run_sample_queries()
    elif choice == "3":
        # 커스텀 이미지 삽입
        insert_custom_image_example()
    else:
        print("❌ 잘못된 선택입니다.")
        print("기본적으로 샘플 쿼리를 실행합니다.")
        run_sample_queries()