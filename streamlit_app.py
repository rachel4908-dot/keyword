"""
네이버 순위 확인기 (by happy) - Streamlit Web App
Copyright ⓒ 2025 happy. All rights reserved.
"""

import streamlit as st
import os
import uuid
import json
import urllib.request
import urllib.parse
import re
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# API 설정
client_id = os.getenv("NAVER_CLIENT_ID")
client_secret = os.getenv("NAVER_CLIENT_SECRET")
naver_ad_access_license = os.getenv("NAVER_AD_ACCESS_LICENSE")
naver_ad_secret_key = os.getenv("NAVER_AD_SECRET_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
UUID_FILE = "user_uuid.txt"

def get_user_id():
    """사용자 UUID 생성 또는 로드"""
    if os.path.exists(UUID_FILE):
        with open(UUID_FILE, "r") as f:
            return f.read().strip()
    new_id = str(uuid.uuid4())
    with open(UUID_FILE, "w") as f:
        f.write(new_id)
    return new_id

def get_public_ip():
    """공용 IP 주소 조회"""
    try:
        with urllib.request.urlopen("https://api.ipify.org") as response:
            return response.read().decode()
    except:
        return "Unknown"

def get_related_keywords(query):
    """네이버에서 연관검색어 조회"""
    try:
        encText = urllib.parse.quote(query)
        url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        response = urllib.request.urlopen(request)
        result = json.loads(response.read())
        
        # 상품 제목에서 키워드 추출
        titles = [re.sub(r"<.*?>", "", item["title"]) for item in result.get("items", [])]
        
        # 키워드 분석 및 연관검색어 생성
        all_words = []
        for title in titles:
            # 공백과 특수문자로 분리
            words = re.findall(r'[가-힣a-zA-Z0-9]+', title)
            all_words.extend(words)
        
        # 단어 빈도 계산 (원래 검색어 제외)
        word_freq = {}
        original_words = set(re.findall(r'[가-힣a-zA-Z0-9]+', query.lower()))
        
        for word in all_words:
            word_lower = word.lower()
            if len(word) >= 2 and word_lower not in original_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순으로 정렬하여 상위 20개 반환
        related_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return [keyword for keyword, freq in related_keywords]
        
    except Exception as e:
        st.error(f"연관검색어 조회 중 오류 발생: {e}")
        return []

def get_top_ranked_product_by_mall(keyword, mall_name, progress_callback=None):
    """네이버 쇼핑에서 특정 쇼핑몰의 최고 순위 상품 검색"""
    encText = urllib.parse.quote(keyword)
    seen_titles = set()
    best_product = None
    
    # 1000개 상품까지 검색 (10페이지)
    for page in range(10):
        start = page * 100 + 1
        url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100&start={start}"
        
        try:
            request = urllib.request.Request(url)
            request.add_header("X-Naver-Client-Id", client_id)
            request.add_header("X-Naver-Client-Secret", client_secret)
            response = urllib.request.urlopen(request)
            result = json.loads(response.read())
            
            # 진행률 업데이트
            if progress_callback:
                progress = int((page + 1) / 10 * 100)
                progress_callback(progress)
            
            for idx, item in enumerate(result.get("items", []), start=1):
                if item.get("mallName") and mall_name in item["mallName"]:
                    title_clean = re.sub(r"<.*?>", "", item["title"])
                    if title_clean in seen_titles:
                        continue
                    seen_titles.add(title_clean)
                    
                    rank = start + idx - 1
                    product = {
                        "rank": rank,
                        "title": title_clean,
                        "price": item["lprice"],
                        "link": item["link"],
                        "mallName": item["mallName"]
                    }
                    
                    if not best_product or rank < best_product["rank"]:
                        best_product = product
                        
        except Exception as e:
            st.error(f"API 요청 오류: {e}")
            break
    
    return best_product

def main():
    """메인 Streamlit 애플리케이션"""
    # 페이지 설정
    st.set_page_config(
        page_title="네이버 순위 확인기 (by happy)",
        page_icon="🔍",
        layout="wide"
    )
    
    # 제목
    st.title("🔍 네이버 순위 확인기 (by happy)")
    st.markdown("---")
    
    # 사이드바에 정보 표시
    with st.sidebar:
        st.header("📊 정보")
        st.info(f"사용자 ID: {get_user_id()[:8]}...")
        st.info(f"IP 주소: {get_public_ip()}")
        st.markdown("---")
        st.markdown("**기능:**")
        st.markdown("• **순위 확인**: 특정 쇼핑몰의 상품 순위 검색")
        st.markdown("• **연관검색어**: 키워드의 연관검색어 조회")
    
    # 탭 생성
    tab1, tab2 = st.tabs(["🎯 순위 확인", "🔗 연관검색어"])
    
    with tab1:
        rank_checker_tab()
    
    with tab2:
        related_keywords_tab()
    
    # 푸터
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; font-size: 12px;'>"
        "ⓒ 2025 happy. 무단 복제 및 배포 금지. All rights reserved."
        "</div>",
        unsafe_allow_html=True
    )

def rank_checker_tab():
    """순위 확인 탭"""
    st.subheader("🎯 순위 확인")
    st.markdown("특정 쇼핑몰에서 상품의 네이버 쇼핑 순위를 확인합니다.")
    
    # 입력 폼
    with st.form("rank_check_form"):
        # 키워드 입력
        keywords_input = st.text_area(
            "검색어 (최대 10개, 쉼표로 구분)",
            placeholder="예: 키보드, 마우스, 충전기",
            height=100,
            help="검색할 상품명들을 쉼표(,)로 구분하여 입력하세요"
        )
        
        # 판매처명 입력
        mall_name = st.text_input(
            "판매처명",
            placeholder="예: OO스토어",
            help="찾고자 하는 쇼핑몰 이름을 입력하세요"
        )
        
        # 제출 버튼
        submitted = st.form_submit_button("🔍 순위 확인", use_container_width=True)
    
    # 폼 제출 처리
    if submitted:
        # 입력 유효성 검사
        if not keywords_input.strip() or not mall_name.strip():
            st.error("⚠️ 검색어와 판매처명을 모두 입력해주세요.")
            return
        
        keywords = [k.strip() for k in keywords_input.split(",") if k.strip()]
        
        if len(keywords) > 10:
            st.error("⚠️ 검색어는 최대 10개까지 입력 가능합니다.")
            return
        
        if not keywords:
            st.error("⚠️ 올바른 검색어를 입력해주세요.")
            return
        
        # 검색 실행
        st.subheader("🔍 검색 결과")
        
        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        all_results = {}
        
        for i, keyword in enumerate(keywords):
            status_text.text(f"검색 중: {keyword} ({i+1}/{len(keywords)})")
            
            def update_progress(progress):
                current_progress = int((i / len(keywords)) * 100 + (progress / len(keywords)))
                progress_bar.progress(min(current_progress, 100))
            
            # 검색 실행
            result = get_top_ranked_product_by_mall(keyword, mall_name, update_progress)
            all_results[keyword] = result
            
            # 결과 표시
            with results_container:
                if result:
                    st.success(f"✅ **{keyword}** - {result['rank']}위 발견!")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**상품명:** {result['title']}")
                        st.write(f"**순위:** {result['rank']}위")
                        st.write(f"**가격:** {int(result['price']):,}원")
                        st.write(f"**쇼핑몰:** {result['mallName']}")
                    
                    with col2:
                        st.link_button("🛒 상품 보기", result['link'])
                    
                    st.markdown("---")
                else:
                    st.error(f"❌ **{keyword}** - 검색 결과 없음")
                    st.markdown("---")
            
            # 최종 진행률 업데이트
            final_progress = int(((i + 1) / len(keywords)) * 100)
            progress_bar.progress(final_progress)
            
            # API 호출 간격 조절
            if i < len(keywords) - 1:
                time.sleep(0.1)
        
        # 검색 완료
        status_text.text("✅ 모든 검색이 완료되었습니다!")
        progress_bar.progress(100)
        
        # 요약 정보
        st.subheader("📊 검색 요약")
        found_count = sum(1 for result in all_results.values() if result is not None)
        total_count = len(keywords)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 검색어", total_count)
        with col2:
            st.metric("발견된 상품", found_count)
        with col3:
            st.metric("발견율", f"{(found_count/total_count*100):.1f}%")

def related_keywords_tab():
    """연관검색어 탭"""
    st.subheader("🔗 연관검색어 조회")
    st.markdown("입력한 키워드와 관련된 연관검색어를 네이버 쇼핑에서 찾아드립니다.")
    
    # 입력 폼
    with st.form("related_keywords_form"):
        query = st.text_input(
            "검색어",
            placeholder="예: 키보드",
            help="연관검색어를 찾을 키워드를 입력하세요"
        )
        
        submitted = st.form_submit_button("🔍 연관검색어 조회", use_container_width=True)
    
    if submitted:
        if not query.strip():
            st.error("⚠️ 검색어를 입력해주세요.")
            return
        
        with st.spinner(f"'{query}' 키워드의 연관검색어를 조회하고 있습니다..."):
            related_keywords = get_related_keywords(query.strip())
        
        if related_keywords:
            st.success(f"✅ '{query}' 키워드의 연관검색어 {len(related_keywords)}개를 찾았습니다!")
            
            # 연관검색어 목록 표시
            st.subheader("📝 연관검색어 목록")
            
            # 3열로 표시
            cols = st.columns(3)
            for i, keyword in enumerate(related_keywords):
                with cols[i % 3]:
                    if st.button(f"🔍 {keyword}", key=f"related_{i}", use_container_width=True):
                        st.session_state.selected_keyword = keyword
                        st.rerun()
            
            # 선택된 키워드로 검색
            if 'selected_keyword' in st.session_state:
                st.info(f"선택된 키워드: **{st.session_state.selected_keyword}**")
                st.markdown("순위 확인 탭에서 이 키워드로 검색해보세요!")
            
            # 텍스트로 복사 가능한 목록
            st.subheader("📋 복사 가능한 목록")
            keywords_text = ", ".join(related_keywords)
            st.text_area(
                "연관검색어 (복사용)",
                value=keywords_text,
                height=100,
                help="이 텍스트를 복사하여 순위 확인 탭에서 사용할 수 있습니다"
            )
            
        else:
            st.warning(f"❌ '{query}' 키워드의 연관검색어를 찾을 수 없습니다.")
            st.info("다른 키워드로 시도해보세요.")

if __name__ == "__main__":
    main()