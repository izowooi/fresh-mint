import os
import boto3
from botocore.config import Config
from pathlib import Path
import mimetypes
from datetime import datetime
import uuid
from typing import Optional, Dict, List
from dotenv import load_dotenv
from PIL import Image

# .env 파일 로드
load_dotenv()


class R2Uploader:
    """Cloudflare R2 이미지 업로드 클래스"""
    
    def __init__(self):
        """R2 업로더 초기화"""
        self.access_key_id = os.getenv("R2_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("R2_SECRET_ACCESS_KEY")
        self.account_id = os.getenv("R2_ACCOUNT_ID")
        self.bucket_name = os.getenv("R2_BUCKET")
        self.public_url = os.getenv("R2_PUBLIC_URL")
        
        # 환경변수 확인
        if not all([self.access_key_id, self.secret_access_key, self.account_id, self.bucket_name]):
            raise ValueError("R2 환경변수가 설정되지 않았습니다!")
        
        self.s3_client = self._create_client()
    
    def _create_client(self):
        """R2 클라이언트 생성"""
        return boto3.client(
            's3',
            endpoint_url=f'https://{self.account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3}
            )
        )
    
    def upload_image(self, file_path: str, key_prefix: str = "") -> Optional[Dict]:
        """
        단일 이미지를 R2에 업로드
        
        Args:
            file_path: 업로드할 이미지 파일 경로
            key_prefix: R2 내 폴더 경로 (예: "2024/01/")
        
        Returns:
            업로드 결과 딕셔너리 또는 None (실패시)
        """
        try:
            # 파일 확인
            if not os.path.exists(file_path):
                print(f"❌ 파일이 존재하지 않습니다: {file_path}")
                return None
            
            file_path_obj = Path(file_path)
            file_name = file_path_obj.name
            
            # 고유 키 생성
            unique_id = uuid.uuid4().hex[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if key_prefix:
                key = f"{key_prefix}/{timestamp}_{unique_id}_{file_name}"
            else:
                key = f"{timestamp}_{unique_id}_{file_name}"
            
            # Content-Type 자동 감지
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # 이미지 메타데이터 추출
            image_info = self._get_image_info(file_path)
            
            # 업로드 메타데이터 설정
            upload_metadata = {
                'upload-date': datetime.now().isoformat(),
                'original-filename': file_name,
                'file-size': str(os.path.getsize(file_path))
            }
            
            # 업로드
            print(f"📤 업로드 중: {file_name}")
            
            with open(file_path, 'rb') as file:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=file,
                    ContentType=content_type,
                    Metadata=upload_metadata
                )
            
            # Public URL 생성
            public_url = f"{self.public_url}/{key}" if self.public_url else f"https://{self.bucket_name}.r2.dev/{key}"
            
            print(f"✅ 업로드 성공: {file_name}")
            
            return {
                'success': True,
                'local_path': file_path,
                'public_url': public_url,
                'r2_key': key,
                'filename': file_name,
                'content_type': content_type,
                'file_size': os.path.getsize(file_path),
                'image_info': image_info,
                'uploaded_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 업로드 실패 {file_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'local_path': file_path
            }
    
    def _get_image_info(self, file_path: str) -> Dict:
        """이미지 파일 정보 추출"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                format_name = img.format.lower() if img.format else 'unknown'
                
                return {
                    'width': width,
                    'height': height,
                    'format': format_name,
                    'mode': img.mode
                }
        except Exception as e:
            print(f"⚠️ 이미지 정보 추출 실패: {str(e)}")
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            return {
                'width': 0,
                'height': 0,
                'format': file_ext or 'unknown',
                'mode': 'unknown'
            }
    
    def upload_folder(
        self, 
        folder_path: str, 
        key_prefix: str = "",
        extensions: List[str] = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    ) -> List[Dict]:
        """
        폴더의 모든 이미지를 R2에 업로드
        
        Args:
            folder_path: 이미지가 있는 폴더 경로
            key_prefix: R2 내 폴더 경로
            extensions: 업로드할 이미지 확장자
        
        Returns:
            업로드 결과 리스트
        """
        results = []
        
        # 폴더 내 이미지 파일 찾기
        image_files = []
        folder_path_obj = Path(folder_path)
        
        for ext in extensions:
            image_files.extend(folder_path_obj.glob(f"*{ext}"))
            image_files.extend(folder_path_obj.glob(f"*{ext.upper()}"))
        
        print(f"📁 {len(image_files)}개의 이미지 파일 발견")
        
        for img_path in image_files:
            result = self.upload_image(str(img_path), key_prefix=key_prefix)
            if result:
                results.append(result)
        
        print(f"✨ 총 {len([r for r in results if r.get('success')])}개 업로드 완료!")
        return results 