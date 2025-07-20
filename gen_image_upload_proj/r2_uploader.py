import os
import boto3
from botocore.config import Config
from pathlib import Path
import mimetypes
from datetime import datetime
import uuid
import io
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
        단일 이미지를 R2에 업로드 (원본 + WebP 변환)
        
        Args:
            file_path: 업로드할 이미지 파일 경로
            key_prefix: 사용하지 않음 (호환성 유지용)
        
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
            file_stem = file_path_obj.stem  # 확장자 제외한 파일명
            
            # 이미지 메타데이터 추출
            image_info = self._get_image_info(file_path)
            
            # 날짜 기반 폴더 생성 (YYMMDD 형식)
            date_folder = datetime.now().strftime("%y%m%d")
            file_ext = file_path_obj.suffix.lower()
            
            # PNG 파일인지 확인
            is_png = file_ext == '.png'
            
            # 1. 원본 파일 업로드 (PNG만)
            original_result = None
            if is_png:
                original_key = f"original/{date_folder}/{file_name}"
                original_result = self._upload_single_file(file_path, original_key, file_name)
                
                if not original_result['success']:
                    return original_result
                
                print(f"✅ PNG 원본 업로드: {file_name}")
            else:
                print(f"⏭️  원본 업로드 생략 ({file_ext}): {file_name}")
            
            # 2. WebP 변환 및 업로드 (모든 파일)
            webp_filename = f"{file_stem}.webp"
            webp_key = f"webp/{date_folder}/{webp_filename}"
            webp_result = self._convert_and_upload_webp(file_path, webp_key, webp_filename)
            
            if not webp_result['success']:
                return webp_result  # WebP 실패시 에러 반환
            
            upload_status = "WebP"
            if is_png:
                upload_status = "원본 + WebP"
            
            print(f"✅ 업로드 완료: {file_name} ({upload_status})")
            
            # 반환 데이터 구성
            result_data = {
                'success': True,
                'local_path': file_path,
                'filename': file_name,
                'image_info': image_info,
                'is_png': is_png,
                'webp': {
                    'public_url': webp_result['public_url'],
                    'r2_key': webp_key,
                    'content_type': 'image/webp',
                    'file_size': webp_result.get('file_size', 0),
                    'success': webp_result['success']
                },
                'uploaded_at': datetime.now().isoformat()
            }
            
            # PNG인 경우에만 원본 정보 추가
            if is_png and original_result:
                result_data['original'] = {
                    'public_url': original_result['public_url'],
                    'r2_key': original_key,
                    'content_type': original_result['content_type'],
                    'file_size': original_result['file_size']
                }
            
            return result_data
            
        except Exception as e:
            print(f"❌ 업로드 실패 {file_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'local_path': file_path
            }
    
    def _upload_single_file(self, file_path: str, key: str, display_name: str) -> Dict:
        """단일 파일을 R2에 업로드"""
        try:
            # Content-Type 자동 감지
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # 업로드 메타데이터 설정
            upload_metadata = {
                'upload-date': datetime.now().isoformat(),
                'original-filename': display_name,
                'file-size': str(os.path.getsize(file_path))
            }
            
            print(f"📤 업로드 중: {display_name} → {key}")
            
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
            
            return {
                'success': True,
                'public_url': public_url,
                'content_type': content_type,
                'file_size': os.path.getsize(file_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_and_upload_webp(self, file_path: str, key: str, display_name: str) -> Dict:
        """이미지를 WebP로 변환하여 업로드"""
        try:
            # PIL로 이미지 열기 및 WebP 변환
            with Image.open(file_path) as img:
                # 원본 크기 정보
                original_width, original_height = img.size
                
                # 새로운 크기 계산 (각각 절반)
                new_width = original_width // 2
                new_height = original_height // 2
                
                print(f"🔄 크기 조정: {original_width}x{original_height} → {new_width}x{new_height}")
                
                # 크기 조정 (고품질 리샘플링)
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # RGB 모드로 변환 (WebP 호환성을 위해)
                if img_resized.mode in ('RGBA', 'LA', 'P'):
                    # 투명도가 있는 경우 RGBA 유지
                    if img_resized.mode == 'P':
                        img_resized = img_resized.convert('RGBA')
                elif img_resized.mode not in ('RGB', 'RGBA'):
                    img_resized = img_resized.convert('RGB')
                
                # 메모리에서 WebP로 변환
                webp_buffer = io.BytesIO()
                img_resized.save(webp_buffer, format='WebP', quality=85, optimize=True)
                webp_buffer.seek(0)
                
                # 업로드 메타데이터 설정
                upload_metadata = {
                    'upload-date': datetime.now().isoformat(),
                    'original-filename': display_name,
                    'converted-from': Path(file_path).suffix.lower(),
                    'file-size': str(webp_buffer.getbuffer().nbytes),
                    'original-size': f"{original_width}x{original_height}",
                    'resized-to': f"{new_width}x{new_height}",
                    'resize-ratio': '0.5x'
                }
                
                print(f"📤 WebP 변환 업로드 중: {display_name} → {key}")
                
                # WebP 파일 업로드
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=webp_buffer.getvalue(),
                    ContentType='image/webp',
                    Metadata=upload_metadata
                )
                
                # Public URL 생성
                public_url = f"{self.public_url}/{key}" if self.public_url else f"https://{self.bucket_name}.r2.dev/{key}"
                
                return {
                    'success': True,
                    'public_url': public_url,
                    'file_size': webp_buffer.getbuffer().nbytes
                }
                
        except Exception as e:
            print(f"⚠️ WebP 변환 실패 {display_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
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