import json
import os


def convert_txt_to_json(input_filepath: str, output_filepath: str):
    """
    텍스트 파일을 읽어 특정 형식의 데이터를 JSON으로 변환합니다.

    Args:
        input_filepath (str): 입력 텍스트 파일의 경로.
        output_filepath (str): 출력 JSON 파일의 경로.
    """
    data = {}

    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()  # 앞뒤 공백 제거

                # 빈 줄, 주석 (#), 섹션 제목 (##) 건너뛰기
                if not line or line.startswith('#'):
                    continue

                # 'ff-XXXXX: ' 패턴 찾기
                if ':' in line:
                    parts = line.split(':', 1)  # 첫 번째 ':' 기준으로 분리
                    key_part = parts[0].strip()
                    prompt_part = parts[1].strip()

                    # 키가 'ff-'로 시작하는지 확인 (원하는 패턴에 맞는지 검증)
                    if key_part.startswith('ff-') and len(key_part) == 8:  # 예: ff-00240
                        data[key_part] = {"prompt": prompt_part}
                    else:
                        print(f"⚠️ 경고: {input_filepath} 파일의 {line_num}번째 줄에서 예상치 못한 형식 발견: '{line}'")
                        print("   'ff-XXXXX:' 패턴을 따르지 않아 건너뜁니다.")
                else:
                    print(f"⚠️ 경고: {input_filepath} 파일의 {line_num}번째 줄에서 ':' 구분자를 찾을 수 없습니다: '{line}'")
                    print("   해당 줄은 건너뜁니다.")

        # JSON 파일로 저장
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        print(f"\n✅ 변환 완료: '{input_filepath}' -> '{output_filepath}'")
        print(f"   총 {len(data)}개의 프롬프트가 JSON으로 저장되었습니다.")

    except FileNotFoundError:
        print(f"❌ 오류: 파일을 찾을 수 없습니다. 경로를 확인해주세요: '{input_filepath}'")
    except Exception as e:
        print(f"❌ 오류 발생 중 파일 처리: {e}")


if __name__ == "__main__":
    # 사용자로부터 입력 및 출력 파일 경로 받기
    input_file = input("변환할 텍스트 파일 경로를 입력하세요 (예: input.txt): ")
    output_file = input("저장할 JSON 파일 경로를 입력하세요 (예: output.json): ")

    # 파일 경로 유효성 검사 (선택 사항)
    if not os.path.exists(input_file):
        print(f"❌ 오류: 입력 파일 '{input_file}'이 존재하지 않습니다.")
    else:
        convert_txt_to_json(input_file, output_file)

