import streamlit as st
import requests
import asyncio
import aiohttp
from typing import List, Dict
import time
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(
   page_title="이미지 갤러리",
   page_icon="🖼️",
   layout="wide",
   initial_sidebar_state="collapsed"
)

# API 엔드포인트
API_URL = "https://image-gallery-api-513122275637.asia-northeast3.run.app/random-images"

# CSS 스타일 정의
st.markdown("""
<style>
   /* 로딩 플레이스홀더 애니메이션 */
   @keyframes shimmer {
       0% { background-position: -1000px 0; }
       100% { background-position: 1000px 0; }
   }

   .loading-placeholder {
       animation: shimmer 2s infinite linear;
       background: linear-gradient(to right, #f0f0f0 4%, #e0e0e0 25%, #f0f0f0 36%);
       background-size: 1000px 100%;
       height: 300px;
       border-radius: 8px;
   }

   /* 이미지 컨테이너 스타일 */
   .image-container {
       position: relative;
       overflow: hidden;
       border-radius: 8px;
       box-shadow: 0 2px 8px rgba(0,0,0,0.1);
       transition: transform 0.3s ease;
       background: #f5f5f5;
   }

   .image-container:hover {
       transform: translateY(-5px);
       box-shadow: 0 4px 12px rgba(0,0,0,0.15);
   }

   /* 정보 아이콘 스타일 */
   .info-button {
       position: absolute;
       bottom: 10px;
       right: 10px;
       background: rgba(255, 255, 255, 0.9);
       border-radius: 50%;
       width: 36px;
       height: 36px;
       display: flex;
       align-items: center;
       justify-content: center;
       cursor: pointer;
       box-shadow: 0 2px 4px rgba(0,0,0,0.2);
       transition: all 0.2s ease;
   }

   .info-button:hover {
       background: rgba(255, 255, 255, 1);
       transform: scale(1.1);
   }

   /* 갤러리 그리드 */
   .gallery-grid {
       display: grid;
       grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
       gap: 20px;
       padding: 20px 0;
   }

   /* 더보기 버튼 스타일 */
   .stButton > button {
       width: 100%;
       background-color: #0066cc;
       color: white;
       font-weight: bold;
       padding: 12px 24px;
       border-radius: 8px;
       border: none;
       transition: all 0.3s ease;
   }

   .stButton > button:hover {
       background-color: #0052a3;
       transform: translateY(-2px);
   }

   /* 헤더 스타일 */
   h1 {
       text-align: center;
       color: #333;
       margin-bottom: 2rem;
   }

   /* 로딩 스피너 */
   .loading-text {
       text-align: center;
       color: #666;
       font-size: 1.1rem;
       margin: 20px 0;
   }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'images' not in st.session_state:
   st.session_state.images = []
if 'loading' not in st.session_state:
   st.session_state.loading = False
if 'initial_load' not in st.session_state:
   st.session_state.initial_load = True
if 'load_more_clicked' not in st.session_state:
   st.session_state.load_more_clicked = False


def fetch_images_async(count: int = 20) -> Dict:
   """이미지를 비동기로 가져오는 함수"""
   try:
       response = requests.get(
           API_URL,
           params={"count": count},
           timeout=30  # 콜드 스타트 고려하여 긴 타임아웃
       )
       response.raise_for_status()
       return response.json()
   except requests.exceptions.RequestException as e:
       st.error(f"이미지 로드 중 오류 발생: {str(e)}")
       return None


def create_image_card(image_data: Dict, index: int):
   """개별 이미지 카드 생성"""
   col_key = f"img_col_{index}_{image_data['id']}"

   # 이미지 컨테이너
   container = st.container()

   with container:
       # 이미지 표시 (placeholder와 함께)
       placeholder = st.empty()

       # 초기 로딩 플레이스홀더 표시
       placeholder.markdown(
           f'<div class="loading-placeholder"></div>',
           unsafe_allow_html=True
       )

       # 실제 이미지 로드 (비동기 효과)
       try:
           # 이미지와 정보 버튼을 포함한 HTML
           image_html = f"""
           <div class="image-container">
               <img src="{image_data['url']}"
                    alt="{image_data['title']}"
                    style="width: 100%; height: auto; display: block; border-radius: 8px;"
                    onload="this.style.opacity='0'; this.style.transition='opacity 0.5s'; setTimeout(() => this.style.opacity='1', 50);">
               <div class="info-button" onclick="console.log('Tags: {json.dumps(image_data["tags"])}'); alert('태그: {", ".join(image_data["tags"])}');">
                   ℹ️
               </div>
           </div>
           """

           # 약간의 지연을 주어 로딩 효과 표시
           time.sleep(0.1)
           placeholder.markdown(image_html, unsafe_allow_html=True)

           # 이미지 제목
           st.caption(f"**{image_data['title']}**")
           
           # 설명 표시 (새로 추가)
           if image_data.get('description'):
               st.caption(f"📝 {image_data['description']}")

           # 메타데이터 표시 (접을 수 있는 형태)
           with st.expander("상세 정보", expanded=False):
               st.write(f"**ID:** {image_data['id']}")
               
               # 태그 프리픽스 표시 (새로 추가)
               if image_data.get('tag_prefix'):
                   st.write(f"**태그 프리픽스:** {image_data['tag_prefix']}")
               
               st.write(f"**크기:** {image_data['metadata']['width']}x{image_data['metadata']['height']} px")
               st.write(f"**포맷:** {image_data['metadata']['format'].upper()}")
               st.write(f"**파일 크기:** {image_data['metadata']['size_kb']} KB")
               
               # WebP URL 표시 (새로 추가)
               if image_data['metadata'].get('webp_url'):
                   st.write(f"**WebP URL:** [링크]({image_data['metadata']['webp_url']})")
               
               # 원본 이미지 정보 (새로 추가)
               if image_data['metadata'].get('has_original'):
                   if image_data['metadata'].get('original_url'):
                       st.write(f"**원본 이미지:** [링크]({image_data['metadata']['original_url']})")
                   else:
                       st.write("**원본 이미지:** 사용 가능")
               else:
                   st.write("**원본 이미지:** 없음")
               
               # 생성 날짜 표시 (새로 추가)
               if image_data.get('created_at'):
                   try:
                       # ISO 형식의 날짜를 파싱
                       created_date = datetime.fromisoformat(image_data['created_at'].replace('Z', '+00:00'))
                       formatted_date = created_date.strftime('%Y년 %m월 %d일 %H:%M')
                       st.write(f"**생성 날짜:** {formatted_date}")
                   except:
                       st.write(f"**생성 날짜:** {image_data['created_at']}")
               
               st.write(f"**태그:** {', '.join(image_data['tags'])}")

       except Exception as e:
           st.error(f"이미지 로드 실패: {str(e)}")


def load_more_images():
   """더 많은 이미지 로드"""
   st.session_state.load_more_clicked = True
   st.session_state.loading = True


# 메인 앱
st.title("🖼️ 이미지 갤러리")
st.markdown("---")

# 초기 로드 또는 더보기 클릭시 이미지 가져오기
if st.session_state.initial_load or st.session_state.load_more_clicked:
   if st.session_state.initial_load:
       st.markdown('<p class="loading-text">🔄 갤러리를 준비하는 중입니다... (첫 로드는 시간이 걸릴 수 있습니다)</p>', unsafe_allow_html=True)

   with st.spinner("이미지를 불러오는 중..."):
       data = fetch_images_async(20)

       if data and 'images' in data:
           st.session_state.images.extend(data['images'])
           st.session_state.initial_load = False
           st.session_state.load_more_clicked = False
           st.session_state.loading = False
           
           # 새로운 응답 구조 정보 표시
           success_message = f"✅ {len(data['images'])}개의 이미지를 불러왔습니다!"
           if data.get('count'):
               success_message += f" (서버에서 {data['count']}개 반환)"
           if data.get('source'):
               success_message += f" [출처: {data['source']}]"
           
           st.success(success_message)
           
           # 타임스탬프 정보 표시 (디버그 정보)
           if data.get('timestamp'):
               st.caption(f"🕒 서버 응답 시각: {data['timestamp']}")
           
           time.sleep(1)
           st.rerun()

# 이미지 갤러리 표시
if st.session_state.images:
   # 갤러리 정보
   st.info(f"📊 총 {len(st.session_state.images)}개의 이미지가 로드되었습니다.")

   # 그리드 레이아웃으로 이미지 표시
   cols_per_row = 4
   rows = len(st.session_state.images) // cols_per_row + (1 if len(st.session_state.images) % cols_per_row else 0)

   image_index = 0
   for row in range(rows):
       cols = st.columns(cols_per_row)
       for col_idx in range(cols_per_row):
           if image_index < len(st.session_state.images):
               with cols[col_idx]:
                   create_image_card(st.session_state.images[image_index], image_index)
               image_index += 1

   # 더보기 버튼
   st.markdown("---")
   col1, col2, col3 = st.columns([1, 2, 1])
   with col2:
       if st.button("🔄 더 많은 이미지 보기", key="load_more", use_container_width=True, disabled=st.session_state.loading):
           load_more_images()
           st.rerun()

# 사이드바 - 갤러리 정보 및 설정
with st.sidebar:
   st.header("📊 갤러리 정보")
   st.write(f"**로드된 이미지:** {len(st.session_state.images)}개")

   if st.button("🔄 갤러리 초기화"):
       st.session_state.images = []
       st.session_state.initial_load = True
       st.rerun()

   st.markdown("---")
   st.caption("💡 각 이미지의 우측 하단 ℹ️ 버튼을 클릭하면 태그 정보를 볼 수 있습니다.")

   # API 상태 체크
   st.markdown("---")
   if st.button("🏥 API 상태 확인"):
       try:
           ping_response = requests.get("https://image-gallery-api-513122275637.asia-northeast3.run.app/ping", timeout=5)
           if ping_response.status_code == 200:
               st.success("✅ API 정상 작동 중")
               st.json(ping_response.json())
           else:
               st.error("❌ API 응답 오류")
       except:
           st.error("❌ API 연결 실패")

# JavaScript 콘솔 로그를 위한 스크립트
st.markdown("""
<script>
// 정보 버튼 클릭 이벤트 처리
document.addEventListener('DOMContentLoaded', function() {
   console.log('갤러리 페이지 로드 완료');
});

// 이미지 로드 모니터링
window.addEventListener('load', function() {
   const images = document.querySelectorAll('img');
   console.log(`총 ${images.length}개의 이미지 감지됨`);
});
</script>
""", unsafe_allow_html=True)

# 푸터
st.markdown("---")
st.markdown(
   "<p style='text-align: center; color: #666;'>Powered by Cloud Run + Cloudflare R2</p>",
   unsafe_allow_html=True
)