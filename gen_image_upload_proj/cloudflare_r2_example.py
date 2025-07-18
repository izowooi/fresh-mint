import os
import boto3
from botocore.config import Config
from pathlib import Path
import mimetypes
from datetime import datetime
import uuid
from typing import Optional, Dict, List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Cloudflare R2 설정
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_BUCKET_NAME = os.getenv("R2_BUCKET")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")


# S3 클라이언트 설정 (R2는 S3 호환 API 사용)
def create_r2_client():
    """R2 클라이언트 생성"""
    return boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(
            signature_version='s3v4',
            retries={'max_attempts': 3}
        )
    )


def upload_image_to_r2(
        file_path: str,
        key_prefix: str = "",
        metadata: Optional[Dict] = None
) -> Optional[str]:
    """
    이미지를 R2에 업로드하고 public URL 반환

    Args:
        file_path: 업로드할 이미지 파일 경로
        key_prefix: R2 내 폴더 경로 (예: "2024/01/")
        metadata: 추가 메타데이터

    Returns:
        public URL 또는 None (실패시)
    """
    try:
        # 파일 확인
        if not os.path.exists(file_path):
            print(f"❌ 파일이 존재하지 않습니다: {file_path}")
            return None

        # R2 클라이언트 생성
        s3_client = create_r2_client()

        # 파일명 생성 (중복 방지를 위해 UUID 추가)
        file_name = Path(file_path).name
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # R2 key 생성 (경로)
        if key_prefix:
            key = f"{key_prefix}/{timestamp}_{unique_id}_{file_name}"
        else:
            key = f"{timestamp}_{unique_id}_{file_name}"

        # Content-Type 자동 감지
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # 메타데이터 설정
        upload_metadata = metadata or {}
        upload_metadata.update({
            'upload-date': datetime.now().isoformat(),
            'original-filename': file_name
        })

        # 업로드
        print(f"📤 업로드 중: {file_name} → {key}")

        with open(file_path, 'rb') as file:
            s3_client.put_object(
                Bucket=R2_BUCKET_NAME,
                Key=key,
                Body=file,
                ContentType=content_type,
                Metadata=upload_metadata
            )

        # Public URL 생성
        public_url = f"{R2_PUBLIC_URL}/{key}"

        print(f"✅ 업로드 성공!")
        print(f"🔗 Public URL: {public_url}")

        return public_url

    except Exception as e:
        print(f"❌ 업로드 실패: {str(e)}")
        return None


def bulk_upload_images(
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
        업로드된 이미지 정보 리스트
    """
    uploaded_images = []

    # 폴더 내 이미지 파일 찾기
    image_files = []
    for ext in extensions:
        image_files.extend(Path(folder_path).glob(f"*{ext}"))
        image_files.extend(Path(folder_path).glob(f"*{ext.upper()}"))

    print(f"📁 {len(image_files)}개의 이미지 파일 발견")

    for img_path in image_files:
        # 이미지 정보 추출 (필요시)
        metadata = {
            'file-size': str(os.path.getsize(img_path)),
            'source-folder': folder_path
        }

        # 업로드
        public_url = upload_image_to_r2(
            str(img_path),
            key_prefix=key_prefix,
            metadata=metadata
        )

        if public_url:
            uploaded_images.append({
                'local_path': str(img_path),
                'public_url': public_url,
                'filename': img_path.name,
                'size': os.path.getsize(img_path),
                'uploaded_at': datetime.now().isoformat()
            })

    return uploaded_images


def list_bucket_contents(prefix: str = "", max_keys: int = 100):
    """버킷 내용 조회"""
    try:
        s3_client = create_r2_client()

        response = s3_client.list_objects_v2(
            Bucket=R2_BUCKET_NAME,
            Prefix=prefix,
            MaxKeys=max_keys
        )

        if 'Contents' in response:
            print(f"\n📋 버킷 내용 ({len(response['Contents'])}개):")
            for obj in response['Contents']:
                print(f"  - {obj['Key']} ({obj['Size']} bytes)")
                print(f"    URL: {R2_PUBLIC_URL}/{obj['Key']}")
        else:
            print("버킷이 비어있습니다.")

    except Exception as e:
        print(f"❌ 조회 실패: {str(e)}")


def delete_from_r2(key: str):
    """R2에서 파일 삭제"""
    try:
        s3_client = create_r2_client()
        s3_client.delete_object(Bucket=R2_BUCKET_NAME, Key=key)
        print(f"✅ 삭제 완료: {key}")
    except Exception as e:
        print(f"❌ 삭제 실패: {str(e)}")


def main():
    """메인 실행 함수"""
    print("🚀 Cloudflare R2 이미지 업로드 스크립트")
    print(f"버킷: {R2_BUCKET_NAME}")
    print(f"Public URL: {R2_PUBLIC_URL}")
    print("-" * 50)

    # 환경변수 확인
    if not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
        print("❌ 환경변수가 설정되지 않았습니다!")
        print("\n📋 .env 파일에 다음을 추가해주세요:")
        print("R2_ACCESS_KEY_ID=your_access_key_id")
        print("R2_SECRET_ACCESS_KEY=your_secret_access_key")
        print("\nCloudflare Dashboard → R2 → Manage R2 API Tokens에서 확인 가능")
        return

    while True:
        print("\n📌 메뉴:")
        print("1. 단일 이미지 업로드")
        print("2. 폴더 전체 업로드")
        print("3. 버킷 내용 조회")
        print("4. 종료")

        choice = input("\n선택 (1-4): ").strip()

        if choice == "1":
            # 단일 이미지 업로드
            file_path = input("이미지 파일 경로: ").strip()
            prefix = input("폴더 경로 (선택사항, 예: 2024/01): ").strip()

            url = upload_image_to_r2(file_path, key_prefix=prefix)
            if url:
                print(f"\n✨ 업로드 완료!")
                print(f"URL: {url}")

        elif choice == "2":
            # 폴더 전체 업로드
            folder_path = input("이미지 폴더 경로: ").strip()
            prefix = input("R2 폴더 경로 (선택사항): ").strip()

            results = bulk_upload_images(folder_path, key_prefix=prefix)
            print(f"\n✨ 총 {len(results)}개 업로드 완료!")

            # 결과 저장 옵션
            if results and input("\n결과를 파일로 저장하시겠습니까? (y/n): ").lower() == 'y':
                import json
                output_file = f"upload_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"📄 결과 저장됨: {output_file}")

        elif choice == "3":
            # 버킷 내용 조회
            prefix = input("조회할 폴더 경로 (전체는 Enter): ").strip()
            list_bucket_contents(prefix)

        elif choice == "4":
            print("👋 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")


# 사용 예시
if __name__ == "__main__":
    # 메인 메뉴 실행
    main()

    # 또는 직접 사용
    # url = upload_image_to_r2("./my_image.jpg", key_prefix="gallery/2024")
    # print(f"Uploaded URL: {url}")