#!/usr/bin/env python3
"""
이미지 업로드 및 DB 저장 메인 플로우

사용법:
    python main_flow.py [옵션]
    
예시:
    # 기본 폴더 ./images 사용
    python main_flow.py
    
    # 특정 폴더 지정
    python main_flow.py --folder /path/to/images
    
    # R2 경로와 배치 크기 지정
    python main_flow.py --folder ./photos --r2-prefix 2024/01 --batch-size 20
    
    # 대화형 모드
    python main_flow.py --interactive
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 모듈 import
from r2_uploader import R2Uploader
from supabase_manager import SupabaseManager


class ImageUploadFlow:
    """이미지 업로드 및 DB 저장 플로우 관리 클래스"""
    
    def __init__(self):
        """플로우 매니저 초기화"""
        try:
            self.r2_uploader = R2Uploader()
            self.supabase_manager = SupabaseManager()
            print("✅ 모든 서비스 연결 완료!")
        except Exception as e:
            print(f"❌ 서비스 초기화 실패: {str(e)}")
            print("\n📋 .env 파일에 다음 환경변수들이 설정되어 있는지 확인해주세요:")
            print("- SUPABASE_URL")
            print("- SUPABASE_ANON_KEY")
            print("- R2_ACCESS_KEY_ID")
            print("- R2_SECRET_ACCESS_KEY")
            print("- R2_ACCOUNT_ID")
            print("- R2_BUCKET")
            print("- R2_PUBLIC_URL")
            sys.exit(1)
    
    def process_folder(self, folder_path: str, r2_prefix: str = "", batch_size: int = 10) -> Dict:
        """
        폴더의 모든 이미지를 처리 (업로드 + DB 저장)
        
        Args:
            folder_path: 처리할 이미지 폴더 경로
            r2_prefix: R2 내 저장할 폴더 경로
            batch_size: DB 배치 삽입 크기
        
        Returns:
            처리 결과 통계
        """
        print(f"🚀 이미지 처리 시작!")
        print(f"📁 폴더: {folder_path}")
        print(f"📦 R2 경로: {r2_prefix or '(루트)'}")
        print("-" * 60)
        
        # 1단계: 폴더 존재 확인
        if not os.path.exists(folder_path):
            print(f"❌ 폴더가 존재하지 않습니다: {folder_path}")
            return {"success": False, "error": "폴더 없음"}
        
        # 2단계: R2에 이미지 업로드
        print("\n📤 1단계: R2에 이미지 업로드 중...")
        upload_results = self.r2_uploader.upload_folder(folder_path, key_prefix=r2_prefix)
        
        if not upload_results:
            print("❌ 업로드할 이미지가 없습니다.")
            return {"success": False, "error": "업로드할 이미지 없음"}
        
        # 성공한 업로드만 필터링
        successful_uploads = [result for result in upload_results if result.get('success')]
        
        print(f"\n📊 업로드 결과:")
        print(f"  - 총 시도: {len(upload_results)}개")
        print(f"  - 성공: {len(successful_uploads)}개")
        print(f"  - 실패: {len(upload_results) - len(successful_uploads)}개")
        
        if not successful_uploads:
            print("❌ 성공한 업로드가 없습니다.")
            return {"success": False, "error": "업로드 실패"}
        
        # 3단계: DB에 이미지 정보 저장
        print("\n💾 2단계: DB에 이미지 정보 저장 중...")
        db_data_list = []
        
        for upload_result in successful_uploads:
            try:
                # 업로드 결과를 DB 데이터로 변환
                db_data = self.supabase_manager.prepare_image_data(upload_result)
                db_data_list.append(db_data)
                
                print(f"📝 데이터 준비 완료: {upload_result['filename'][:30]}...")
                print(f"   - ID: {db_data['id']}")
                print(f"   - 제목: {db_data['title']}")
                print(f"   - 태그 접두어: {db_data['tag_prefix']}")
                
            except Exception as e:
                print(f"⚠️ 데이터 준비 실패 {upload_result['filename']}: {str(e)}")
        
        # 배치 삽입
        print(f"\n📊 {len(db_data_list)}개 아이템 DB 삽입 시작 (배치 크기: {batch_size})...")
        db_result = self.supabase_manager.insert_images_batch(db_data_list, batch_size)
        
        # 4단계: 결과 정리
        final_result = {
            "success": True,
            "folder_path": folder_path,
            "r2_prefix": r2_prefix,
            "upload_stats": {
                "total_attempted": len(upload_results),
                "upload_successful": len(successful_uploads),
                "upload_failed": len(upload_results) - len(successful_uploads)
            },
            "db_stats": db_result,
            "processed_at": datetime.now().isoformat()
        }
        
        # 결과 출력
        self._print_final_results(final_result)
        
        return final_result
    
    def _print_final_results(self, result: Dict):
        """최종 결과 출력"""
        print("\n" + "=" * 60)
        print("🎉 처리 완료!")
        print("=" * 60)
        
        upload_stats = result["upload_stats"]
        db_stats = result["db_stats"]
        
        print(f"📤 업로드 결과:")
        print(f"  - 시도: {upload_stats['total_attempted']}개")
        print(f"  - 성공: {upload_stats['upload_successful']}개")
        print(f"  - 실패: {upload_stats['upload_failed']}개")
        
        print(f"\n💾 DB 저장 결과:")
        print(f"  - 성공: {db_stats['total_inserted']}개")
        print(f"  - 실패: {db_stats['failed_count']}개")
        print(f"  - 성공률: {db_stats['success_rate']}%")
        
        if db_stats['failed_count'] > 0:
            print(f"\n⚠️ 실패한 아이템들:")
            for item in db_stats['failed_items'][:5]:  # 처음 5개만 표시
                print(f"  - {item.get('title', 'Unknown')}")
    
    def save_results(self, result: Dict, output_file: str = None):
        """결과를 JSON 파일로 저장"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"upload_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 결과가 저장되었습니다: {output_file}")


def main():
    """메인 실행 함수"""
    print("🎯 이미지 업로드 & DB 저장 플로우")
    print("=" * 60)
    
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(description='이미지 폴더를 R2에 업로드하고 Supabase DB에 메타데이터를 저장합니다.')
    parser.add_argument('--folder', 
                        default="/Users/izowooi/Downloads/temp/Firefly",
                        help='처리할 이미지 폴더 경로 (기본값: /Users/izowooi/Downloads/temp/Firefly)')
    parser.add_argument('--r2-prefix',
                        default="",
                        help='R2 내 저장할 폴더 경로 (기본값: 루트)')
    parser.add_argument('--batch-size',
                        type=int,
                        default=10,
                        help='DB 배치 삽입 크기 (기본값: 10)')
    parser.add_argument('--interactive',
                        action='store_true',
                        help='대화형 모드로 실행')

    args = parser.parse_args()
    
    # 대화형 모드인 경우
    if args.interactive:
        print("\n🔧 대화형 모드")
        folder_path = input(f"이미지 폴더 경로 (기본값: {args.folder}): ").strip() or args.folder
        r2_prefix = input(f"R2 폴더 경로 (기본값: {args.r2_prefix or '루트'}): ").strip() or args.r2_prefix
        batch_size = args.batch_size
        
        try:
            batch_input = input(f"배치 크기 (기본값: {args.batch_size}): ").strip()
            if batch_input:
                batch_size = int(batch_input)
        except ValueError:
            print(f"⚠️ 잘못된 배치 크기입니다. 기본값 {args.batch_size}를 사용합니다.")
            batch_size = args.batch_size
    else:
        folder_path = args.folder
        r2_prefix = args.r2_prefix
        batch_size = args.batch_size
    
    print(f"\n📁 처리할 폴더: {folder_path}")
    print(f"📦 R2 경로: {r2_prefix or '(루트)'}")
    print(f"📊 배치 크기: {batch_size}")
    print("-" * 60)
    
    # 플로우 실행
    try:
        flow = ImageUploadFlow()
        result = flow.process_folder(folder_path, r2_prefix, batch_size)

        # 결과 저장 여부 확인
        if result.get("success") and input("\n결과를 JSON 파일로 저장하시겠습니까? (y/n): ").lower() == 'y':
            flow.save_results(result)

        # 통계 조회
        if input("\n현재 DB 통계를 확인하시겠습니까? (y/n): ").lower() == 'y':
            stats = flow.supabase_manager.get_image_stats()
            if stats:
                print("\n📊 현재 DB 통계:")
                print(f"  - 총 이미지: {stats['total_images']}개")
                print(f"  - 태그 접두어별 통계:")
                for prefix, count in stats['prefix_stats'].items():
                    print(f"    • {prefix}: {count}개")

    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 처리 중 오류 발생: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 