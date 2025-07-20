import os
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# .env 파일 로드
load_dotenv()


class SupabaseManager:
    """Supabase 데이터베이스 관리 클래스"""
    
    def __init__(self):
        """Supabase 매니저 초기화"""
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        # 환경변수 확인
        if not self.url or not self.key:
            raise ValueError("Supabase 환경변수가 설정되지 않았습니다!")
        
        self.client: Client = create_client(self.url, self.key)
    
    def extract_tag_prefix(self, filename: str) -> str:
        """
        파일명에서 FF-00010 형태의 태그 접두어 추출
        
        Args:
            filename: 파일명 (예: "Firefly_ff-00220 Mysterious portrait of  793926 g0y.jpg")
        
        Returns:
            추출된 태그 접두어 (예: "FF-00220") 또는 "UNKNOWN"
        """
        # 패턴: ff-숫자 또는 FF-숫자
        pattern = r'([a-zA-Z]{2}-\d{5})'
        match = re.search(pattern, filename, re.IGNORECASE)
        
        if match:
            return match.group(1).upper()
        else:
            return "UNKNOWN"
    
    def prepare_image_data(self, upload_result: Dict, custom_data: Optional[Dict] = None) -> Dict:
        """
        R2 업로드 결과를 기반으로 DB 삽입용 데이터 준비
        
        Args:
            upload_result: R2 업로드 결과 딕셔너리
            custom_data: 추가 커스텀 데이터
        
        Returns:
            DB 삽입용 이미지 데이터
        """
        if not upload_result.get('success'):
            raise ValueError("업로드 실패한 파일은 DB에 삽입할 수 없습니다")
        
        filename = upload_result['filename']
        image_info = upload_result.get('image_info', {})
        
        # 고유 ID 생성
        image_id = f"img_{uuid.uuid4().hex[:8]}"
        
        # 타이틀: 파일명의 앞 20글자
        title = filename[:20]
        if len(filename) > 20:
            title += "..."
        
        # 태그 접두어 추출
        tag_prefix = self.extract_tag_prefix(filename)
        
        # 메타데이터 구성
        metadata = {
            "width": image_info.get('width', 0),
            "height": image_info.get('height', 0),
            "format": image_info.get('format', 'unknown'),
            "size_kb": round(upload_result.get('file_size', 0) / 1024, 2),
            "content_type": upload_result.get('content_type', 'unknown'),
            "r2_key": upload_result.get('r2_key', ''),
            "uploaded_at": upload_result.get('uploaded_at', datetime.now().isoformat())
        }
        
        # 커스텀 데이터 병합
        if custom_data:
            metadata.update(custom_data)
        
        # DB 삽입용 데이터 구성
        image_data = {
            "id": image_id,
            "url": upload_result['public_url'],
            "title": title,
            "tags": ["test", "sample"],  # 더미 태그
            "tag_prefix": tag_prefix,
            "metadata": metadata
        }
        
        return image_data
    
    def insert_image(self, image_data: Dict) -> Optional[Dict]:
        """
        단일 이미지 데이터를 DB에 삽입
        
        Args:
            image_data: 삽입할 이미지 데이터
        
        Returns:
            삽입 결과 또는 None (실패시)
        """
        try:
            # 데이터 유효성 검사
            if not self._validate_image_data(image_data):
                return None
            
            response = self.client.table('images').insert(image_data).execute()
            print(f"✅ DB 삽입 성공: {image_data['id']} ({image_data['title']})")
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ DB 삽입 실패: {image_data.get('id', 'unknown')} - {str(e)}")
            return None
    
    def insert_images_batch(self, images_data: List[Dict], batch_size: int = 50) -> Dict:
        """
        다중 이미지 데이터를 배치로 DB에 삽입
        
        Args:
            images_data: 삽입할 이미지 데이터 리스트
            batch_size: 배치 크기
        
        Returns:
            삽입 결과 통계
        """
        total_inserted = 0
        failed_count = 0
        failed_items = []
        
        print(f"📊 총 {len(images_data)}개 아이템을 {batch_size}개씩 배치 처리합니다...")
        
        # 배치로 나누어 처리
        for i in range(0, len(images_data), batch_size):
            batch = images_data[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            try:
                response = self.client.table('images').insert(batch).execute()
                inserted_count = len(response.data)
                total_inserted += inserted_count
                print(f"✅ 배치 {batch_num} 완료: {inserted_count}개 삽입")
                
            except Exception as e:
                print(f"❌ 배치 {batch_num} 실패: {str(e)}")
                print("개별 삽입 시도 중...")
                
                # 실패한 배치는 개별 삽입 시도
                for item in batch:
                    result = self.insert_image(item)
                    if result:
                        total_inserted += 1
                    else:
                        failed_count += 1
                        failed_items.append(item)
        
        return {
            'total_inserted': total_inserted,
            'failed_count': failed_count,
            'failed_items': failed_items,
            'success_rate': round((total_inserted / len(images_data)) * 100, 1) if images_data else 0
        }
    
    def _validate_image_data(self, image_data: Dict) -> bool:
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
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터 유효성 검사 실패: {str(e)}")
            return False
    
    def get_image_stats(self) -> Optional[Dict]:
        """이미지 통계 조회"""
        try:
            # 전체 개수
            count_response = self.client.table('images').select("*", count='exact').execute()
            total_count = count_response.count
            
            # 태그 접두어별 통계
            all_images = self.client.table('images').select("tag_prefix").execute()
            prefix_counts = {}
            
            for img in all_images.data:
                prefix = img.get('tag_prefix', 'UNKNOWN')
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
            
            # 최근 업로드
            recent_images = self.client.table('images')\
                .select("title, created_at")\
                .order("created_at", desc=True)\
                .limit(5).execute()
            
            return {
                "total_images": total_count,
                "prefix_stats": prefix_counts,
                "recent_uploads": recent_images.data
            }
            
        except Exception as e:
            print(f"❌ 통계 조회 실패: {str(e)}")
            return None 