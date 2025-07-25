#!/usr/bin/env python3
"""
ComfyUI 프롬프트 추출기 CLI
SOLID 원칙에 맞게 설계된 모듈화된 프롬프트 추출 도구
"""

import sys
import argparse
from pathlib import Path
from prompt_processor import create_default_processor


def process_single_image_command(args):
    """단일 이미지 처리 명령"""
    processor = create_default_processor()

    success = processor.process_single_image(
        image_path=args.image_path,
        output_path=args.output_path
    )

    if success:
        print("\n🎉 단일 이미지 처리가 완료되었습니다!")
    else:
        print("\n❌ 단일 이미지 처리에 실패했습니다.")
        sys.exit(1)


def process_folder_command(args):
    """폴더 배치 처리 명령"""
    processor = create_default_processor()

    success_count = processor.process_folder(
        folder_path=args.folder_path,
        output_file=args.output_file
    )

    if success_count > 0:
        print(f"\n🎉 폴더 처리가 완료되었습니다! ({success_count}개 성공)")
    else:
        print("\n❌ 폴더 처리에서 성공한 파일이 없습니다.")
        sys.exit(1)


def interactive_mode():
    """대화형 모드"""
    print("🤖 ComfyUI 프롬프트 추출기")
    print("=" * 40)

    while True:
        print("\n선택하세요:")
        print("1. 단일 이미지 처리")
        print("2. 폴더 배치 처리")
        print("3. 종료")

        choice = input("\n선택 (1-3): ").strip()

        if choice == "1":
            image_path = input("이미지 파일 경로를 입력하세요: ").strip().strip('"')
            if not image_path:
                print("❌ 경로가 입력되지 않았습니다.")
                continue

            output_path = input("출력 파일 경로 (엔터 시 기본값): ").strip().strip('"')
            output_path = output_path if output_path else None

            processor = create_default_processor()
            success = processor.process_single_image(image_path, output_path)

            if success:
                print("✅ 처리 완료!")
            else:
                print("❌ 처리 실패!")

        elif choice == "2":
            folder_path = input("폴더 경로를 입력하세요: ").strip().strip('"')
            if not folder_path:
                print("❌ 경로가 입력되지 않았습니다.")
                continue

            output_file = input("출력 파일 경로 (예: prompts.txt): ").strip().strip('"')
            if not output_file:
                output_file = "output/batch_prompts.txt"
                print(f"기본값 사용: {output_file}")

            processor = create_default_processor()
            success_count = processor.process_folder(folder_path, output_file)

            if success_count > 0:
                print(f"✅ {success_count}개 파일 처리 완료!")
            else:
                print("❌ 처리된 파일이 없습니다!")

        elif choice == "3":
            print("👋 프로그램을 종료합니다.")
            break

        else:
            print("❌ 잘못된 선택입니다. 1-3 중에서 선택하세요.")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description="ComfyUI 이미지에서 긍정 프롬프트를 추출하는 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
 # 대화형 모드
 python main_cli.py

 # 단일 이미지 처리
 python main_cli.py single image.png
 python main_cli.py single image.png -o custom_output.txt

 # 폴더 배치 처리
 python main_cli.py folder /path/to/images -o batch_prompts.txt
       """
    )

    subparsers = parser.add_subparsers(dest='command', help='사용할 명령')

    # 단일 이미지 처리 명령
    single_parser = subparsers.add_parser('single', help='단일 이미지 처리')
    single_parser.add_argument('image_path', help='처리할 이미지 파일 경로')
    single_parser.add_argument(
        '-o', '--output-path',
        help='출력 텍스트 파일 경로 (기본값: output/이미지이름.txt)'
    )

    # 폴더 배치 처리 명령
    folder_parser = subparsers.add_parser('folder', help='폴더 배치 처리')
    folder_parser.add_argument('folder_path', help='이미지가 있는 폴더 경로')
    folder_parser.add_argument(
        '-o', '--output-file',
        default='output/batch_prompts.txt',
        help='출력 파일 경로 (기본값: output/batch_prompts.txt)'
    )

    args = parser.parse_args()

    # 명령어 처리
    if args.command == 'single':
        process_single_image_command(args)
    elif args.command == 'folder':
        process_folder_command(args)
    else:
        # 명령어가 없으면 대화형 모드
        interactive_mode()


if __name__ == "__main__":
    main()