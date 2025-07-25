import json
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, List
from PIL import Image
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PromptResult:
    """프롬프트 추출 결과를 담는 데이터 클래스"""
    positive_prompt: Optional[str]
    success: bool
    error_message: Optional[str] = None


class ImageMetadataReader(ABC):
    """이미지 메타데이터를 읽는 인터페이스"""

    @abstractmethod
    def read_workflow_data(self, image_path: str) -> Optional[dict]:
        pass

    @abstractmethod
    def can_handle(self, image_info: dict) -> bool:
        """이 리더가 해당 이미지 정보를 처리할 수 있는지 확인"""
        pass


class ComfyUIMetadataReader(ImageMetadataReader):
    """ComfyUI 이미지의 메타데이터를 읽는 구현체"""

    def can_handle(self, image_info: dict) -> bool:
        """ComfyUI 형식인지 확인"""
        return 'workflow' in image_info or 'prompt' in image_info

    def read_workflow_data(self, image_path: str) -> Optional[dict]:
        """ComfyUI 이미지에서 워크플로우 데이터를 추출합니다."""
        try:
            with Image.open(image_path) as img:
                # workflow 또는 prompt 키에서 메타데이터를 찾습니다
                workflow_str = img.info.get('workflow') or img.info.get('prompt')

            if not workflow_str:
                return None

            return json.loads(workflow_str)

        except (FileNotFoundError, json.JSONDecodeError, Exception):
            return None


class ParametersMetadataReader(ImageMetadataReader):
    """parameters 형식의 메타데이터를 읽는 구현체 (WebUI 등)"""

    def can_handle(self, image_info: dict) -> bool:
        """parameters 형식인지 확인"""
        # parameters 키가 직접 있거나, metadata 안에 parameters가 있는 경우
        if 'parameters' in image_info:
            return True
        if 'metadata' in image_info:
            metadata = image_info['metadata']
            if isinstance(metadata, dict) and 'parameters' in metadata:
                return True
        return False

    def read_workflow_data(self, image_path: str) -> Optional[dict]:
        """parameters 형식에서 메타데이터를 추출합니다."""
        try:
            with Image.open(image_path) as img:
                image_info = img.info

                # parameters 키 찾기
                parameters_str = None
                if 'parameters' in image_info:
                    parameters_str = image_info['parameters']
                elif 'metadata' in image_info:
                    metadata = image_info['metadata']
                    if isinstance(metadata, dict) and 'parameters' in metadata:
                        parameters_str = metadata['parameters']

                if not parameters_str:
                    return None

                # parameters 문자열을 파싱하여 워크플로우 형태로 변환
                return self._parse_parameters_string(parameters_str)

        except (FileNotFoundError, Exception):
            return None

    def _parse_parameters_string(self, parameters_str: str) -> dict:
        """parameters 문자열을 파싱하여 프롬프트를 추출합니다."""
        # Negative prompt: 를 기준으로 분할
        parts = parameters_str.split('\nNegative prompt:', 1)

        positive_prompt = parts[0].strip()

        # 워크플로우 형태로 변환 (ComfyUI와 호환되도록)
        return {
            'format': 'parameters',
            'positive_prompt': positive_prompt,
            'negative_prompt': parts[1].split('\n')[0].strip() if len(parts) > 1 else "",
            'raw_parameters': parameters_str
        }


class MetadataReaderFactory:
    """적절한 메타데이터 리더를 선택하는 팩토리 클래스"""

    def __init__(self):
        self.readers = [
            ComfyUIMetadataReader(),
            ParametersMetadataReader()
        ]

    def get_reader(self, image_path: str) -> Optional[ImageMetadataReader]:
        """이미지에 적합한 리더를 반환합니다."""
        try:
            with Image.open(image_path) as img:
                image_info = img.info

                for reader in self.readers:
                    if reader.can_handle(image_info):
                        return reader

            return None

        except Exception:
            return None


class PromptExtractor(ABC):
    """프롬프트를 추출하는 인터페이스"""

    @abstractmethod
    def extract_positive_prompt(self, workflow_data: dict) -> PromptResult:
        pass


class ComfyUIPromptExtractor(PromptExtractor):
    """ComfyUI 워크플로우에서 프롬프트를 추출하는 구현체"""

    def extract_positive_prompt(self, workflow_data: dict) -> PromptResult:
        """워크플로우 데이터에서 긍정 프롬프트를 추출합니다."""
        try:
            # parameters 형식인지 확인
            if workflow_data.get('format') == 'parameters':
                return self._extract_from_parameters(workflow_data)

            # ComfyUI 형식 처리
            return self._extract_from_comfyui(workflow_data)

        except Exception as e:
            return PromptResult(None, False, f"프롬프트 추출 중 오류: {str(e)}")

    def _extract_from_parameters(self, workflow_data: dict) -> PromptResult:
        """parameters 형식에서 프롬프트를 추출합니다."""
        positive_prompt = workflow_data.get('positive_prompt')
        if positive_prompt:
            return PromptResult(positive_prompt.strip(), True)
        return PromptResult(None, False, "parameters에서 긍정 프롬프트를 찾을 수 없습니다")

    def _extract_from_comfyui(self, workflow_data: dict) -> PromptResult:
        """ComfyUI 형식에서 프롬프트를 추출합니다."""
        if 'nodes' not in workflow_data:
            return PromptResult(None, False, "워크플로우에 nodes 정보가 없습니다")

        nodes = {str(node['id']): node for node in workflow_data['nodes']}

        # 방법 1: 노드 제목이 'Positive'인 경우를 먼저 찾습니다
        prompt = self._find_by_title(nodes)
        if prompt:
            return PromptResult(prompt.strip(), True)

        # 방법 2: 샘플러 연결을 추적합니다
        prompt = self._find_by_sampler_connection(nodes, workflow_data)
        if prompt:
            return PromptResult(prompt.strip(), True)

        return PromptResult(None, False, "긍정 프롬프트를 찾을 수 없습니다")

    def _find_by_title(self, nodes: dict) -> Optional[str]:
        """제목으로 Positive 노드를 찾습니다."""
        for node in nodes.values():
            if node['type'] == 'CLIPTextEncode':
                node_title = node.get('title', '').strip()
                if node_title.lower() == 'positive':
                    return node.get('widgets_values', [''])[0]
        return None

    def _find_by_sampler_connection(self, nodes: dict, workflow_data: dict) -> Optional[str]:
        """샘플러 연결을 추적하여 프롬프트를 찾습니다."""
        # 샘플러 노드 찾기
        sampler_node = self._find_sampler_node(nodes)
        if not sampler_node:
            return None

        # positive 입력 링크 찾기
        positive_input = next(
            (i for i in sampler_node.get('inputs', []) if i['name'] == 'positive'),
            None
        )
        if not positive_input or 'link' not in positive_input:
            return None

        # 링크를 통해 프롬프트 노드 찾기
        origin_node_id = self._find_origin_node_id(
            positive_input['link'],
            workflow_data.get('links', [])
        )
        if not origin_node_id:
            return None

        # 프롬프트 텍스트 추출
        prompt_node = nodes.get(str(origin_node_id))
        if prompt_node and prompt_node['type'] == 'CLIPTextEncode':
            return prompt_node.get('widgets_values', [''])[0]

        return None

    def _find_sampler_node(self, nodes: dict) -> Optional[dict]:
        """샘플러 노드를 찾습니다."""
        sampler_types = ['KSampler', 'KSampler (Efficient)', 'workflow>ScheduledCFG']
        for node in nodes.values():
            if node['type'] in sampler_types:
                return node
        return None

    def _find_origin_node_id(self, link_id: int, links: List) -> Optional[int]:
        """링크 ID로 원본 노드 ID를 찾습니다."""
        for link_info in links:
            if link_info[0] == link_id:
                return link_info[1]
        return None


class UniversalMetadataReader(ImageMetadataReader):
    """모든 형식을 자동으로 처리하는 통합 리더"""

    def __init__(self):
        self.factory = MetadataReaderFactory()

    def can_handle(self, image_info: dict) -> bool:
        """항상 처리 시도"""
        return True

    def read_workflow_data(self, image_path: str) -> Optional[dict]:
        """적절한 리더를 찾아서 워크플로우 데이터를 읽습니다."""
        reader = self.factory.get_reader(image_path)
        if reader:
            return reader.read_workflow_data(image_path)
        return None


class FileManager:
    """파일 관리를 담당하는 클래스"""

    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

    def save_single_prompt(self, prompt: str, image_path: str, output_path: Optional[str] = None) -> str:
        """단일 프롬프트를 파일로 저장합니다."""
        if output_path:
            save_path = Path(output_path)
        else:
            # output 폴더에 이미지 이름으로 저장
            image_name = Path(image_path).stem
            save_path = self.base_output_dir / f"{image_name}.txt"

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

        return str(save_path)

    def append_prompt_to_file(self, prompt: str, output_file: str):
        """프롬프트를 파일에 append로 추가합니다."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'a', encoding='utf-8') as f:
            f.write(f"{prompt}\n")

    def get_image_files(self, folder_path: str) -> List[str]:
        """폴더에서 이미지 파일들을 찾습니다."""
        folder = Path(folder_path)
        if not folder.exists():
            return []

        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        image_files = []

        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))

        return sorted(image_files)


class PromptProcessor:
    """프롬프트 처리의 전체 흐름을 조율하는 클래스"""

    def __init__(self,
                 metadata_reader: ImageMetadataReader,
                 prompt_extractor: PromptExtractor,
                 file_manager: FileManager):
        self.metadata_reader = metadata_reader
        self.prompt_extractor = prompt_extractor
        self.file_manager = file_manager

    def process_single_image(self, image_path: str, output_path: Optional[str] = None) -> bool:
        """단일 이미지에서 프롬프트를 추출하여 파일로 저장합니다."""
        print(f"처리 중: {image_path}")

        # 워크플로우 데이터 읽기
        workflow_data = self.metadata_reader.read_workflow_data(image_path)
        if not workflow_data:
            print(f"❌ 워크플로우 데이터를 읽을 수 없습니다: {image_path}")
            return False

        # 데이터 형식 확인 및 출력
        data_format = workflow_data.get('format', 'comfyui')
        print(f"📋 감지된 형식: {data_format}")

        # 프롬프트 추출
        result = self.prompt_extractor.extract_positive_prompt(workflow_data)
        if not result.success:
            print(f"❌ 프롬프트 추출 실패: {result.error_message}")
            return False

        if not result.positive_prompt:
            print("❌ 추출된 프롬프트가 비어있습니다")
            return False

        # 파일 저장
        try:
            saved_path = self.file_manager.save_single_prompt(
                result.positive_prompt,
                image_path,
                output_path
            )
            print(f"✅ 성공: {saved_path}")
            return True

        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")
            return False

    def process_folder(self, folder_path: str, output_file: str) -> int:
        """폴더 내 모든 이미지의 프롬프트를 하나의 파일에 저장합니다."""
        print(f"폴더 처리 중: {folder_path}")

        # 이미지 파일 목록 가져오기
        image_files = self.file_manager.get_image_files(folder_path)
        if not image_files:
            print("❌ 폴더에 이미지 파일이 없습니다")
            return 0

        print(f"발견된 이미지 파일: {len(image_files)}개")

        success_count = 0

        for image_path in image_files:
            print(f"\n처리 중: {Path(image_path).name}")

            # 워크플로우 데이터 읽기
            workflow_data = self.metadata_reader.read_workflow_data(image_path)
            if not workflow_data:
                print(f"❌ 워크플로우 데이터를 읽을 수 없습니다")
                continue

            # 데이터 형식 확인
            data_format = workflow_data.get('format', 'comfyui')
            print(f"📋 형식: {data_format}")

            # 프롬프트 추출
            result = self.prompt_extractor.extract_positive_prompt(workflow_data)
            if not result.success:
                print(f"❌ 프롬프트 추출 실패: {result.error_message}")
                continue

            if not result.positive_prompt:
                print("❌ 추출된 프롬프트가 비어있습니다")
                continue

            # 파일에 append
            try:
                self.file_manager.append_prompt_to_file(result.positive_prompt, output_file)
                print(f"✅ 추가됨: {len(result.positive_prompt)} 문자")
                success_count += 1

            except Exception as e:
                print(f"❌ 파일 저장 실패: {e}")
                continue

        print(f"\n📊 결과: {success_count}/{len(image_files)} 개 성공")
        print(f"📁 저장 위치: {output_file}")

        return success_count


def create_default_processor() -> PromptProcessor:
    """기본 설정으로 PromptProcessor를 생성합니다."""
    metadata_reader = UniversalMetadataReader()  # 모든 형식 자동 처리
    prompt_extractor = ComfyUIPromptExtractor()  # 확장된 추출기
    file_manager = FileManager()

    return PromptProcessor(metadata_reader, prompt_extractor, file_manager)


