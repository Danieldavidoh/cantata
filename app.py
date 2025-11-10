import json
import os
import uuid
import base64
import random
import streamlit as st
from datetime import datetime, date, timedelta
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
from math import radians, cos, sin, asin, sqrt, atan2, degrees
import requests
import pandas as pd  # 추가: pandas 필요

# --- 파일 저장 경로 설정 ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 가짜 라이브러리 임포트 (st_autorefresh는 Streamlit 환경에서만 유효)
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = lambda **kwargs: None

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 자동 새로고침 ---
# 관리자가 아닐 경우 10초마다 새로고침
if not st.session_state.get("admin", False):
    st_autorefresh(interval=10000, key="auto_refresh_user")

# --- 파일 경로 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
USER_POST_FILE = "user_posts.json"

# --- 1. 다국어 설정 ---
LANG = {
    "ko": {
        "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
        "tab_notice": "공지", "tab_map": "투어 경로", "indoor": "실내", "outdoor": "실외",
        "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
        "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
        "add_city": "추가", "register": "등록", "update": "수정", "remove": "제거",
        "date": "날짜", "city_name": "도시 이름", "search_placeholder": "도시/장소 검색...",
        
        # 추가 번역 (모든 UI 요소 포함)
        "general": "일반", "urgent": "긴급",
        "admin_login": "관리자 로그인",
        "update_content": "내용 수정",
        "existing_notices": "기존 공지사항",
        "no_notices": "공지사항이 없습니다.",
        "content": "내용",
        "no_content": "내용 없음",
        "no_title": "제목 없음",
        "tour_schedule_management": "투어 일정 관리",
        "set_data": "데이터 설정",
        "type": "유형",
        "city": "도시",
        "link": "링크",
        "past_route": "지난 경로",
        "single_location": "단일 위치",
        "legend": "범례",
        "no_schedule": "일정이 없습니다.",
        "city_coords_error": "좌표를 찾을 수 없습니다. city_dict에 추가해 주세요.",
        "logged_in_success": "관리자로 로그인했습니다.",
        "logged_out_success": "로그아웃했습니다.",
        "incorrect_password": "비밀번호가 틀렸습니다.",
        "fill_in_fields": "제목과 내용을 채워주세요.",
        "notice_reg_success": "공지사항이 성공적으로 등록되었습니다!",
        "notice_del_success": "공지사항이 삭제되었습니다.",
        "notice_upd_success": "공지사항이 수정되었습니다.",
        "schedule_reg_success": "일정이 등록되었습니다.",
        "schedule_del_success": "일정 항목이 제거되었습니다.",
        "schedule_upd_success": "일정이 성공적으로 수정되었습니다.",
        "venue_placeholder": "공연 장소를 입력하세요",
        "note_placeholder": "특이사항을 입력하세요",
        "google_link_placeholder": "구글맵 URL을 입력하세요",
        "seats_tooltip": "예상 관객 인원",
        "file_attachment": "파일 첨부",
        "attached_files": "첨부 파일",
        "no_files": "없음",
        "user_posts": "사용자 포스트", 
        "new_post": "새 포스트 작성", 
        "post_content": "포스트 내용", 
        "media_attachment": "사진/동영상 첨부", 
        "post_success": "포스트가 성공적으로 업로드되었습니다!", 
        "no_posts": "현재 포스트가 없습니다.", 
        "admin_only_files": "첨부 파일은 관리자만 확인 가능합니다.", 
        "probability": "가능성",  # 수정됨: (%) 제거
        "select_city": "도시 선택",  # 추가: 왼쪽 UI용
        "add_city_btn": "추가",  # 추가
        "venues_dates": "도시 목록 및 날짜",  # 추가
        "performance_date": "공연 날짜",  # 추가
        "date_changed": "날짜 변경됨",  # 추가
        "add_venue": "공연장 추가",  # 추가
        "venue_name": "공연장 이름",  # 추가
        "indoor_outdoor": "실내/실외",  # 추가
        "enter_venue_name": "공연장 이름을 입력하세요",  # 추가
        "venue_registered": "공연장 등록됨",  # 추가
        "navigate": "길찾기",  # 추가
        "save": "저장",  # 추가
        "caption": "지도 설명",  # 추가
        "date_format": "%Y-%m-%d"  # 추가
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        # ... (나머지 en 번역 그대로)
        "probability": "Probability",  # 수정됨
        # 추가 키들 영어로
        "select_city": "Select City",
        "add_city_btn": "Add",
        "venues_dates": "Venues & Dates",
        "performance_date": "Performance Date",
        "date_changed": "Date Changed",
        "add_venue": "Add Venue",
        "venue_name": "Venue Name",
        "indoor_outdoor": "Indoor/Outdoor",
        "enter_venue_name": "Enter venue name",
        "venue_registered": "Venue Registered",
        "navigate": "Navigate",
        "save": "Save",
        "caption": "Map Caption",
        "date_format": "%Y-%m-%d"
    },
    "hi": {
        "title_cantata": "कंटटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        # ... (나머지 hi 번역 그대로)
        "probability": "संभावना",  # 수정됨
        # 추가 키들 힌디어로
        "select_city": "शहर चुनें",
        "add_city_btn": "जोड़ें",
        "venues_dates": "स्थान और तिथियां",
        "performance_date": "प्रदर्शन तिथि",
        "date_changed": "तिथि बदली गई",
        "add_venue": "स्थान जोड़ें",
        "venue_name": "स्थल नाम",
        "indoor_outdoor": "इनडोर/आउटडोर",
        "enter_venue_name": "स्थल नाम दर्ज करें",
        "venue_registered": "स्थल पंजीकृत",
        "navigate": "नेविगेट",
        "save": "सहेजें",
        "caption": "मानचित्र कैप्शन",
        "date_format": "%Y-%m-%d"
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False,
            "route": [], "dates": {}, "venues": {}, "admin_venues": {}, "guest_mode": False, "expanded_cities": []}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state[k], str): st.session_state[k] = "ko"

# --- 번역 함수 ---
def _(key):
    lang = st.session_state.lang if isinstance(st.session_state.lang, str) else "ko"
    return LANG.get(lang, LANG["ko"]).get(key, key)

# --- 파일 첨부/저장 함수 ---
def save_uploaded_files(uploaded_files):
    file_info_list = []
    for uploaded_file in uploaded_files:
        unique_filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        try:
            with open(file_path, "wb") as f: 
                f.write(uploaded_file.getbuffer())
            file_info_list.append({"name": uploaded_file.name, "path": file_path, "type": uploaded_file.type, "size": uploaded_file.size})
        except Exception: 
            pass
    return file_info_list

# --- 파일 Base64 인코딩 함수 (추가) ---
def get_file_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: 
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception: 
        return None

# --- 미디어 인라인 표시 및 다운로드 헬퍼 함수 ---
def display_and_download_file(file_info, notice_id, is_admin=False, is_user_post=False):
    file_size_kb = round(file_info['size'] / 1024, 1)
    file_type = file_info['type']; file_path = file_info['path']; file_name = file_info['name']
    key_prefix = "admin" if is_admin else "user"
    
    if is_user_post and not is_admin:
        st.markdown(f"**{_('attached_files')}:** {_('admin_only_files')}")
        return

    if os.path.exists(file_path):
        if file_type.startswith('image/'):
            base64_data = get_file_as_base64(file_path)
            if base64_data:
                st.image(f"data:{file_type};base64,{base64_data}", caption=f"🖼️ {file_name} ({file_size_kb} KB)", use_column_width=True)
            else:
                st.markdown(f"**🖼️ {file_name} ({file_size_kb} KB)** (다운로드 버튼)")
                try: 
                    with open(file_path, "rb") as f: 
                        st.download_button(label=f"⬇️ {file_name} 다운로드", data=f.read(), file_name=file_name, mime=file_type, key=f"{key_prefix}_download_{notice_id}_{file_name}_imgfallback")
                except Exception: 
                    pass
            
        elif file_type.startswith('video/'):
            st.video(open(file_path, 'rb').read(), format=file_type, start_time=0)
            st.markdown(f"**🎬 {file_name} ({file_size_kb} KB)**")
            
        else:
            icon = "📄"
            try: 
                with open(file_path, "rb") as f: 
                    st.download_button(label=f"⬇️ {icon} {file_name} ({file_size_kb} KB)", data=f.read(), file_name=file_name, mime=file_type, key=f"{key_prefix}_download_{notice_id}_{file_name}")
            except Exception: 
                pass
    else:
        st.markdown(f"**{file_name}** (파일을 찾을 수 없습니다.)")

# --- JSON 헬퍼 ---
def load_json(f):
    if os.path.exists(f):
        try: 
            with open(f, "r", encoding="utf-8") as file: 
                return json.load(file)
        except json.JSONDecodeError: 
            return []
    return []

def save_json(f, d):
    try: 
        with open(f, "w", encoding="utf-8") as file: 
            json.dump(d, file, ensure_ascii=False, indent=2)
    except Exception: 
        pass
        
# --- 거리 및 시간 계산 함수 ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반지름 (km)

    lat1, lon1 = radians(lat1), radians(lon1)
    lat2, lon2 = radians(lat2), radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    distance = R * c
    return distance

def calculate_distance_and_time(p1, p2):
    lat1, lon1 = p1
    lat2, lon2 = p2
    distance_km = haversine(lat1, lon1, lat2, lon2)
    
    avg_speed_kmh = 60 if distance_km < 500 else 80
        
    travel_time_h = distance_km / avg_speed_kmh
    
    distance_str = f"{distance_km:.1f} km"
    
    hours = int(travel_time_h)
    minutes = int((travel_time_h - hours) * 60)
    
    time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

    return f"거리: {distance_str} | 예상 시간: {time_str}"

# --- 5. 도시 목록 및 좌표 정의 ---
city_dict = {
    # ... (전체 city_dict 그대로 복사. 생략했지만 원본 그대로)
}

# 데이터 로드
tour_notices = load_json(NOTICE_FILE)
tour_schedule = load_json(CITY_FILE)
user_posts = load_json(USER_POST_FILE)

# cities 정의 (tour_schedule에서 추출)
cities = list(set(item['city'] for item in tour_schedule if 'city' in item))  # 중복 제거

# cols 정의 (공연장 테이블 컬럼)
cols = ["Venue", "Seats", "IndoorOutdoor", "Google Maps Link", "Special Notes", "Probability"]

# --- 6. 제목 (TypeError 고침) ---
lang = st.session_state.lang
title_text = f"{_('title_cantata')} {_('title_year')} {_('title_region')}"

if lang == "ko":
    parts = title_text.split()
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{" ".join(parts[1:])}</span>'
else:
    parts = title_text.rsplit(" ", 1)
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{parts[1] if len(parts)>1 else ""}</span>'
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)

# --- 7. 헬퍼 ---
def target(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(c): d = st.session_state.dates.get(c); return d.strftime(_["date_format"]) if d else "TBD"
# 구글 지도 길찾기 링크 생성 함수
def nav(url): 
    return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

# --- 8. 왼쪽 컬럼 ---
left, right = st.columns([1,3])
with left:
    # 도시 추가 UI (도시 추가 시 중복 방지)
    avail = [c for c in cities if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([2,1])
        with c1:
            next_city = st.selectbox(_["select_city"], avail, key="next_city_select_v2")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True) 
            if st.button(_["add_city_btn"], key="add_city_btn_v2"):
                st.session_state.route.append(next_city)
                st.rerun()
    st.markdown("---")
    
    # 등록된 도시 목록
    if st.session_state.route:
        st.subheader(_["venues_dates"])
        
        for city in st.session_state.route:
            t = target()
            has = city in t and not t.get(city, pd.DataFrame()).empty
            
            # Expander Title / Icon Logic
            nav_link = ""
            venue_count = len(t[city]) if has else 0
            if has and not t[city].empty:
                first_link = t[city].iloc[0].get("Google Maps Link", "")
                if first_link and first_link.startswith("http"):
                    nav_link = nav(first_link)
            
            icon_in_title = f' <a href="{nav_link}" target="_blank" style="text-decoration:none;font-size:1.2em;">🚗</a>' if nav_link else ''
            
            title_html_content = f"**{city}** – {date_str(city)} ({venue_count} {_['venue']}){icon_in_title}"

            with st.expander(title_html_content, expanded=False, key=f"expander_{city}"):
                
                # 1. 공연 날짜 입력 (달력만 사용)
                cur = st.session_state.dates.get(city, datetime.now().date())
                new = st.date_input(_["performance_date"], cur, key=f"date_{city}_v2")
                if new != cur: st.session_state.dates[city] = new; st.success(_["date_changed"]); st.rerun()
                
                # 2. 등록 폼 (관리자/손님 모드일 때만)
                if st.session_state.admin or st.session_state.guest_mode:
                    
                    st.markdown("---")
                    st.markdown(f"**{_['add_venue']}**")
                    
                    with st.form(key=f"add_venue_form_{city}_v3", clear_on_submit=True):
                        # 공연장 이름 & 좌석 수
                        col1, col2 = st.columns([3,1])
                        with col1: venue_name = st.text_input(_["venue_name"], key=f"v_{city}_v3")
                        with col2: seats = st.number_input(_["seats"], 1, step=50, key=f"s_{city}_v3")
                        
                        # 구글 링크 & 실내/실외 & 확률
                        col_l, col_s, col_ug, col_up = st.columns(4)
                        type_options_map = {_["indoor"]: "indoor", _["outdoor"]: "outdoor"} 
                        selected_type = col_l.selectbox(_["indoor_outdoor"], list(type_options_map.keys()), key=f"io_{city}_v3", label_visibility="visible")
                        type_sel = type_options_map[selected_type]
                        
                        expected_seats = col_s.number_input(_["seats"], min_value=0, value=500, step=50, key=f"expected_seats_{city}")
                        google_link = col_ug.text_input(_["google_link"], placeholder=_["google_link_placeholder"], key=f"l_{city}_v3")
                        probability = col_up.slider(_["probability"], min_value=0, max_value=100, value=100, step=5, key=f"prob_{city}")

                        note = st.text_area(_["note"], placeholder=_["note_placeholder"], key=f"sn_{city}_v3")
                        
                        submitted = st.form_submit_button(_["register"])
                        
                        if submitted:
                            if not venue_name: st.error(_["enter_venue_name"])
                            else:
                                new_row = pd.DataFrame([{"Venue": venue_name, "Seats": seats, "IndoorOutdoor": selected_type, "Google Maps Link": google_link, "Special Notes": note, "Probability": probability}])
                                t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), new_row], ignore_index=True)
                                st.success(_["venue_registered"])
                                st.session_state.expanded_cities = []
                                st.rerun()

                # 3. 등록된 공연장 목록 표시 (편집/삭제 기능 포함)
                if has:
                    st.markdown("---")
                    for idx, row in t[city].iterrows():
                        st.markdown(f'<div style="border: 1px dashed #228B22; padding: 10px; margin-bottom: 10px; border-radius: 8px;">', unsafe_allow_html=True)
                        
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                        
                        with col1: 
                            st.write(f"**{row['Venue']}**")
                            st.caption(f"{row['Seats']} {_['seats']} | {_['probability']}: {row.get('Probability', 100)}%")
                        with col2:
                            color_icon = "🔵" if row["IndoorOutdoor"] == _["indoor"] else "🟢"
                            st.write(f"{color_icon} {row['IndoorOutdoor']}")
                        
                        with col3:
                            if row["Google Maps Link"].startswith("http"):
                                nav_url = nav(row["Google Maps Link"])
                                st.markdown(f'<a href="{nav_url}" target="_blank" style="font-weight: bold; text-decoration: none; color: #FFD700;">🚗 {_["navigate"]}</a>', unsafe_allow_html=True)
                        
                        with col4:
                            edit_key = f"edit_{city}_{idx}_v2"
                            if st.button(_["update"], key=f"edit_btn_{city}_{idx}_v2"): st.session_state[edit_key] = True; st.rerun()
                            
                        with col5:
                            if st.button(_["remove"], key=f"del_btn_{city}_{idx}_v2"):
                                t[city] = t[city].drop(idx).reset_index(drop=True)
                                if t[city].empty: t.pop(city, None)
                                st.success(_["schedule_del_success"])
                                st.rerun()
                                
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # 수정 폼 (예시, 실제 구현 필요)
                        if st.session_state.get(edit_key, False):
                            with st.form(f"edit_form_{city}_{idx}_v2"):
                                # 수정 필드들...
                                if st.form_submit_button(_["save"]):
                                    # 저장 로직...
                                    st.session_state[edit_key] = False
                                    st.rerun()

# --- 9. 오른쪽 컬럼 – 지도 ---
with right:
    st.markdown("---")
    st.subheader(f"🗺️ {_('tab_map')} 보기")

    current_date = date.today()
    schedule_for_map = sorted([s for s in tour_schedule if s.get('date') and s.get('lat') is not None and s.get('lon') is not None and s.get('id')], key=lambda x: x['date'])
    
    AURANGABAD_COORDS = city_dict.get("Aurangabad", {'lat': 19.876165, 'lon': 75.343314})
    start_coords = [AURANGABAD_COORDS['lat'], AURANGABAD_COORDS['lon']]
    
    m = folium.Map(location=start_coords, zoom_start=8, tiles="CartoDB positron")
    locations = []
    
    for item in schedule_for_map:
        # ... (지도 마커/팝업 코드 그대로. 생략했지만 원본 그대로)
    
    # ... (AntPath 및 거리/시간 라벨 코드 그대로)

    st_folium(m, width=700, height=500, key="tour_map_render")
    
    st.caption(_["caption"])
