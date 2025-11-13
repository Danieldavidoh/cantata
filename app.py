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
from requests.utils import quote # URL 인코딩을 위해 import
import textwrap # 들여쓰기 문제 해결을 위해 import
import re # 정규식 사용을 위해 추가

# --- 파일 저장 경로 설정 ---
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 가짜 라이브러리 임포트 (st_autorefresh는 Streamlit 환경에서만 유효)
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    # Streamlit 환경이 아닐 경우 dummy 함수 정의
    st_autorefresh = lambda **kwargs: None

st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# --- 파일 경로 ---
NOTICE_FILE = "notice.json"
CITY_FILE = "cities.json"
USER_POST_FILE = "user_posts.json"

# --- 1. 다국어 설정 ---
LANG = {
    "ko": {
        "title_cantata": "칸타타 투어", "title_year": "2025", "title_region": "마하라스트라",
        "tab_notice": "공지", "tab_map": "칸타타 투어", "indoor": "실내", "outdoor": "실외", 
        "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
        "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
        "add_city": "추가", "register": "등록", "update": "수정", "remove": "제거",
        "date": "날짜", "city_name": "도시 이름", "search_placeholder": "도시/장소 검색...",
        "general": "일반", "urgent": "긴급", "admin_login": "관리자 로그인", "update_content": "내용 수정",
        "existing_notices": "기존 공지사항", "no_notices": "공지사항이 없습니다。", "content": "내용",
        "no_content": "내용 없음", "no_title": "제목 없음", 
        "tour_schedule_management": "공연도시 정보 입력", 
        "venue_list_title": "공연 도시 목록", 
        "set_data": "데이터 설정", "type": "유형", "city": "도시", "link": "링크", "past_route": "지난 경로",
        "single_location": "단일 위치", "legend": "범례", "no_schedule": "일정이 없습니다。",
        "city_coords_error": "좌표를 찾을 수 없습니다. city_dict에 추가해 주세요。",
        "logged_in_success": "관리자로 로그인했습니다。", "logged_out_success": "로그아웃했습니다。",
        "incorrect_password": "비밀번호가 틀렸습니다。", "fill_in_fields": "제목과 내용을 채워주세요。",
        "notice_reg_success": "공지사항이 성공적으로 등록되었습니다!", "notice_del_success": "공지사항이 삭제되었습니다。",
        "notice_upd_success": "공지사항이 수정되었습니다。", "schedule_reg_success": "일정이 등록되었습니다。",
        "schedule_del_success": "일정 항목이 제거되었습니다。", "schedule_upd_success": "일정이 성공적으로 수정되었습니다。",
        "venue_placeholder": "공연 장소를 입력하세요", "note_placeholder": "특이사항을 입력하세요",
        "google_link_placeholder": "장소 이름(예: Dagdusheth Halwai Ganpati) 또는 URL", 
        "seats_tooltip": "예상 관객 인원",
        "file_attachment": "파일 첨부", "attached_files": "첨부 파일", "no_files": "없음",
        "user_posts": "사용자 포스트",
        "new_post": "새 포스트 작성",
        "post_content": "포스트 내용",
        "media_attachment": "사진/동영상 첨부",
        "post_success": "포스트가 성공적으로 업로드되었습니다!",
        "no_posts": "현재 포스트가 없습니다。",
        "admin_only_files": "첨부 파일은 관리자만 확인 가능합니다。", 
        "probability": "가능성",
        "caption": "지도 위의 아이콘이나 경로를 클릭하여 세부 정보를 확인하세요。",
        "delete_all_data": "전체 데이터 영구 삭제",
        "delete_all_warning": "경고: 모든 공지, 일정 및 사용자 포스트가 영구 삭제됩니다. 계속하시려면 비밀번호를 입력하세요。",
        "delete_all_confirm": "정말로 모든 데이터를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다!",
        "delete_all_success": "모든 데이터가 성공적으로 삭제되었습니다!",
        "no_show": "공연없음"
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Cantata Tour", "indoor": "Indoor", "outdoor": "Outdoor", 
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date", "city_name": "City Name", "search_placeholder": "Search City/Venue...",
        "general": "General", "urgent": "Urgent", "admin_login": "Admin Login", "update_content": "Update Content",
        "existing_notices": "Existing Notices", "no_notices": "No notices available.", "content": "Content",
        "no_content": "No Content", "no_title": "No Title", 
        "tour_schedule_management": "Venue Information Input", 
        "venue_list_title": "Venue City List", 
        "set_data": "Set Data", "type": "Type", "city": "City", "link": "Link", "past_route": "Past Route",
        "single_location": "Single Location", "legend": "Legend", "no_schedule": "No schedule available.",
        "city_coords_error": "Coordinates not found. Please add to city_dict.", "logged_in_success": "Logged in as Admin.",
        "logged_out_success": "Logged out.", "incorrect_password": "Incorrect password.",
        "fill_in_fields": "Please fill in the title and content.", "notice_reg_success": "Notice registered successfully!",
        "notice_del_success": "Notice deleted.", "notice_upd_success": "Notice updated.",
        "schedule_reg_success": "Schedule registered.", "schedule_del_success": "Schedule entry removed.",
        "schedule_upd_success": "Schedule updated successfully.", "venue_placeholder": "Enter venue name",
        "note_placeholder": "Enter notes/special remarks",
        "google_link_placeholder": "Venue Name (e.g., Dagdusheth Halwai Ganpati) or URL",
        "seats_tooltip": "Expected audience count",
        "file_attachment": "File Attachment", "attached_files": "Attached Files", "no_files": "None",
        "user_posts": "User Posts",
        "new_post": "Create New Post",
        "post_content": "Post Content",
        "media_attachment": "Attach Photo/Video",
        "post_success": "Post uploaded successfully!",
        "no_posts": "No posts available.",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "Probability",
        "caption": "Click icons or routes on the map for details.",
        "delete_all_data": "Permanently Delete All Data",
        "delete_all_warning": "Warning: All notices, schedules, and user posts will be permanently deleted. Enter password to proceed.",
        "delete_all_confirm": "Are you sure you want to delete ALL data? This action is irreversible!",
        "delete_all_success": "All data successfully deleted!",
        "no_show": "No Show"
    },
    "hi": {
        "title_cantata": "कंटटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "कंटटा टूर", "indoor": "इनडोर", "outdoor": "आउटडोर", 
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख", "city_name": "शहर का नाम", "search_placeholder": "शहर/स्थल खोजें...",
        "general": "सामान्य", "urgent": "तत्काल", "admin_login": "व्यवस्थापक लॉगिन", "update_content": "सामग्री अपडेट करें",
        "existing_notices": "मौजूदा सूचनाएं", "no_notices": "कोई सूचना उपलब्ध नहीं है।", "content": "सामग्री",
        "no_content": "कोई सामग्री नहीं", "no_title": "कोई शीर्षक नहीं", 
        "tour_schedule_management": "प्रदर्शन शहर की जानकारी इनपुट", 
        "venue_list_title": "प्रदर्शन शहर की सूची", 
        "set_data": "डेटा सेट करें", "type": "प्रकार", "city": "शहर", "link": "लिंक", "past_route": "पिछला मार्ग",
        "single_location": "एकल स्थान", "legend": "किंवंती", "no_schedule": "कोई कार्यक्रम उपलब्ध नहीं है।",
        "city_coords_error": "निर्देशांक नहीं मिला। कृपया city_dict में जोड़ें।", "logged_in_success": "व्यवस्थापक के रूप में लॉग इन किया गया।",
        "logged_out_success": "लॉग आउट किया गया।", "incorrect_password": "गलत पासवर्ड।",
        "fill_in_fields": "कृपया शीर्षक और सामग्री भरें।", "notice_reg_success": "सूचना सफलतापूर्वक पंजीकृत हुई!",
        "notice_del_success": "सूचना हटा दी गई।", "notice_upd_success": "सूचना अपडेट की गई।",
        "schedule_reg_success": "कार्यक्रम पंजीकृत हुआ।", "schedule_del_success": "कार्यक्रम प्रविष्टि हटा दी गई।",
        "schedule_upd_success": "कार्यक्रम सफलतापूर्वक अपडेट किया गया।", "venue_placeholder": "स्थल का नाम दर्ज करें",
        "note_placeholder": "नोट्स/विशेष टिप्पणी दर्ज करें",
        "google_link_placeholder": "स्थल का नाम (उदा: दगडूशेठ हलवाई गणपति) या URL",
        "seats_tooltip": "अपेक्षित दर्शक संख्या",
        "file_attachment": "फ़ाइल संलग्नक", "attached_files": "संलग्न फ़ाइलें", "no_files": "कोई नहीं",
        "user_posts": "उपयोगकर्ता पोस्ट", "new_post": "नई पोस्ट बनाएं", "post_content": "Post सामग्री",
        "media_attachment": "फोटो/वीडियो संलग्न करें", "post_success": "पोस्ट सफलतापूर्वक अपलोड हुई!", "no_posts": "कोई पोस्ट उपलब्ध नहीं है.",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "संभावना",
        "caption": "विवरण के लिए मानचित्र पर आइकन या मार्गों पर क्लिक करें।",
        "delete_all_data": "Permanently Delete All Data",
        "delete_all_warning": "Warning: All notices, schedules, and user posts will be permanently deleted. Enter password to proceed.",
        "delete_all_confirm": "Are you sure you want to delete ALL data? This action is irreversible!",
        "delete_all_success": "All data successfully deleted!",
        "no_show": "कोई शो नहीं"
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False, "show_controls": False, "current_tab_index": 0} 
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state[k], str): st.session_state[k] = "ko"

# --- 관리자 및 UI 설정 ---
ADMIN_PASS = "0009"

# === 활동 감지 및 자동 로그아웃 로직 ===
if "last_activity_time" not in st.session_state:
    st.session_state.last_activity_time = datetime.now()

def update_activity():
    """활동 시간을 현재 시간으로 갱신합니다."""
    st.session_state.last_activity_time = datetime.now()

update_activity()


# 1. 자동 로그아웃 검사
if st.session_state.admin:
    # 1초마다 자동 새로고침 설정 (관리자 모드에서만)
    st_autorefresh(interval=1000, key="auto_refresh_admin") 
    
    time_since_last_activity = (datetime.now() - st.session_state.last_activity_time).total_seconds()
    TIMEOUT_SECONDS = 120 
    
    if time_since_last_activity > TIMEOUT_SECONDS:
        st.session_state.admin = False
        st.session_state.logged_in_user = None
        st.info("관리자 활동이 2분 이상 없어 자동으로 로그아웃되었습니다.")
        st.session_state.show_controls = False
        st.session_state.show_login_form = False
        st.rerun()
# === 활동 감지 및 자동 로그아웃 로직 끝 ===


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
            with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
            file_info_list.append({"name": uploaded_file.name, "path": file_path, "type": uploaded_file.type, "size": uploaded_file.size})
        except Exception: pass
    return file_info_list

# --- 파일 Base64 인코딩 함수 (추가) ---
def get_file_as_base64(file_path):
    """파일 경로를 받아 Base64 문자열을 반환합니다."""
    try:
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode('utf-8')
    except Exception: return None

# --- 미디어 인라인 표시 및 다운로드 헬퍼 함수 ---
def display_and_download_file(file_info, item_id, is_admin=False, is_user_post=False):
    file_size_kb = round(file_info.get('size', 0) / 1024, 1)
    file_type = file_info.get('type', 'application/octet-stream')
    file_path = file_info.get('path', '')
    file_name = file_info.get('name', 'Unknown File')
    key_prefix = "admin" if is_admin else "user"

    if is_user_post and not is_admin:
        st.markdown(f"**{file_name}** ({_('admin_only_files')})")
        return

    if os.path.exists(file_path):
        # 1. 인라인 표시 (이미지/비디오)
        if file_type.startswith('image/'):
            base64_data = get_file_as_base64(file_path)
            if base64_data:
                st.image(f"data:{file_type};base64,{base64_data}", caption=f"🖼️ {file_name} ({file_size_kb} KB)", use_container_width=True)
            else:
                st.markdown(f"**🖼️ {file_name} ({file_size_kb} KB)** (다운로드 버튼)")
        elif file_type.startswith('video/'):
            try:
                # Streamlit video widget requires file content or path, but in environment without direct file access, only path works
                # For robustness, we try to read and use the download button for inline display fallback.
                st.video(open(file_path, 'rb').read(), format=file_type, start_time=0)
                st.markdown(f"**🎬 {file_name} ({file_size_kb} KB)**")
            except Exception:
                 st.markdown(f"**🎬 {file_name} ({file_size_kb} KB)**")
        else:
            icon = "📄"
            st.markdown(f"**{icon} {file_name} ({file_size_kb} KB)**")

        # 2. 다운로드 버튼 (모든 파일)
        try:
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ {file_name} 다운로드", 
                    data=f.read(), 
                    file_name=file_name, 
                    mime=file_type, 
                    key=f"downloader_{key_prefix}_{item_id}_{file_name}"
                )
        except Exception:
            st.error(f"Error reading file {file_name}.")
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
    """두 위도/경도 쌍 사이의 지구 표면 거리를 km 단위로 계산합니다 (Haversine 공식)."""
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
    """
    두 좌표 사이의 거리와 예상 소요 시간을 문자열로 반환합니다. 
    평균 속도 50 km/h를 가정하며, 시간은 'Xh Ym' 형식으로 표기합니다.
    """
    lat1, lon1 = p1
    lat2, lon2 = p2
    distance_km = haversine(lat1, lon1, lat2, lon2)

    # 모든 평균 속도를 50 km/h로 설정
    avg_speed_kmh = 50 

    travel_time_h_decimal = distance_km / avg_speed_kmh
    
    # 시간을 시(h)와 분(m)으로 분리
    hours = int(travel_time_h_decimal)
    minutes_decimal = travel_time_h_decimal - hours
    minutes = round(minutes_decimal * 60)
    
    # 거리 포맷 (km)
    distance_str = f"{distance_km:.0f} km"
    
    # 시간 포맷을 'Xh Ym' 형식으로 변경
    time_str = f"{hours}h {minutes}m"

    return f"{distance_str} / {time_str}"

# --- 5. 도시 목록 및 좌표 정의 ---
city_dict = {
    "Ahmadnagar": {"lat": 19.095193, "lon": 74.749596}, "Akola": {"lat": 20.702269, "lon": 77.004699},
    "Ambernath": {"lat": 19.186354, "lon": 73.191948}, "Amravati": {"lat": 20.93743, "lon": 77.779271},
    "Adul": {"lat": 19.98, "lon": 75.35},
    "Aurangabad": {"lat": 19.876165, "lon": 75.343314}, "Badlapur": {"lat": 19.1088, "lon": 73.1311},
    "Bandra": {"lat": 19.0544, "lon": 72.8406},
    "Bazar": {"lat": 20.75, "lon": 77.05},
    "Bhandara": {"lat": 21.180052, "lon": 79.564987}, "Bhiwandi": {"lat": 19.300282, "lon": 73.069645},
    "Bhusawal": {"lat": 21.02606, "lon": 75.830095},
    "Buldhana": {"lat": 20.5312, "lon": 76.1706},
    "Chandrapur": {"lat": 19.957275, "lon": 79.296875},
    "Chiplun": {"lat": 17.5322, "lon": 73.516}, "Dhule": {"lat": 20.904964, "lon": 74.774651},
    "Dombivli": {"lat": 19.2183, "lon": 73.0865}, "Gondia": {"lat": 21.4598, "lon": 80.195},
    "Hingoli": {"lat": 19.7146, "lon": 77.1424}, "Ichalkaranji": {"lat": 16.6956, "lon": 74.4561},
    "Jalgaon": {"lat": 21.007542, "lon": 75.562554}, "Jalna": {"lat": 19.833333, "lon": 75.883333},
    "Jawla": {"lat": 19.50, "lon": 77.30},
    "Kalyan": {"lat": 19.240283, "lon": 73.13073}, "Karad": {"lat": 17.284, "lon": 74.1779},
    "Karanja": {"lat": 20.7083, "lon": 76.93}, "Karanja Lad": {"lat": 20.3969, "lon": 76.8908},
    "Karjat": {"lat": 18.9121, "lon": 73.3259}, "Kavathe Mahankal": {"lat": 17.218, "lon": 74.416},
    "Khamgaon": {"lat": 20.691, "lon": 76.6886}, "Khopoli": {"lat": 18.6958, "lon": 73.3207},
    "Kodoli": {"lat": 16.8764, "lon": 74.1909},
    "Kolad": {"lat": 18.5132, "lon": 73.2166}, "Kolhapur": {"lat": 16.691031, "lon": 74.229523},
    "Kopargaon": {"lat": 19.883333, "lon": 74.483333}, "Koparkhairane": {"lat": 19.0873, "lon": 72.9856},
    "Kothrud": {"lat": 18.507399, "lon": 73.807648}, "Kudal": {"lat": 16.033333, "lon": 73.683333},
    "Kurla": {"lat": 19.0667, "lon": 72.8833}, "Latur": {"lat": 18.406526, "lon": 76.560229},
    "Lonavala": {"lat": 18.75, "lon": 73.4}, "Mahad": {"lat": 18.086, "lon": 73.3006},
    "Malegaon": {"lat": 20.555256, "lon": 74.525539}, "Malkapur": {"lat": 20.4536, "lon": 76.3886},
    "Manmad": {"lat": 20.3333, "lon": 74.4333}, 
    "Mira Road": {"lat": 19.2799, "lon": 72.8561},
    "Mira-Bhayandar": {"lat": 19.271112, "lon": 72.854094},
    "Miraj": {"lat": 16.8295, "lon": 74.6433},
    "Mumbai": {"lat": 19.07609, "lon": 72.877426}, "Nagpur": {"lat": 21.1458, "lon": 79.088154},
    "Nanded": {"lat": 19.148733, "lon": 77.321011}, "Nandurbar": {"lat": 21.317, "lon": 74.02},
    "Nashik": {"lat": 20.011645, "lon": 73.790332}, "Niphad": {"lat": 20.074, "lon": 73.834},
    "Osmanabad": {"lat": 18.169111, "lon": 76.035309}, "Palghar": {"lat": 19.691644, "lon": 72.768478},
    "Panaji": {"lat": 15.4909, "lon": 73.8278}, "Panvel": {"lat": 18.989746, "lon": 73.117069},
    "Paratwada": {"lat": 21.3019, "lon": 77.5178},
    "Parbhani": {"lat": 19.270335, "lon": 76.773347}, "Peth": {"lat": 18.125, "lon": 74.514},
    "Phaltan": {"lat": 17.9977, "lon": 74.4066}, "Pune": {"lat": 18.52043, "lon": 73.856743},
    "Raigad": {"lat": 18.515048, "lon": 73.179436}, "Ramtek": {"lat": 21.3142, "lon": 79.2676},
    "Ratnagiri": {"lat": 16.990174, "lon": 73.311902}, "Sangli": {"lat": 16.855005, "lon": 74.56427},
    "Sangole": {"lat": 17.126, "lon": 75.0331}, "Saswad": {"lat": 18.3461, "lon": 74.0335},
    "Satara": {"lat": 17.688481, "lon": 73.993631}, "Sawantwadi": {"lat": 15.8964, "lon": 73.7626},
    "Shahada": {"lat": 21.1167, "lon": 74.5667}, "Shirdi": {"lat": 19.7667, "lon": 74.4771},
    "Shirpur": {"lat": 21.1286, "lon": 74.4172}, "Shirur": {"lat": 18.7939, "lon": 74.0305},
    "Shrirampur": {"lat": 19.6214, "lon": 73.8653}, "Sinnar": {"lat": 19.8531, "lon": 73.9976},
    "Solan": {"lat": 30.9083, "lon": 77.0989}, "Solapur": {"lat": 17.659921, "lon": 75.906393},
    "Talegaon": {"lat": 18.7519, "lon": 73.487}, "Thane": {"lat": 19.218331, "lon": 72.978088},
    "Wadala": {"lat": 19.0216, "lon": 72.8646},
    "Achalpur": {"lat": 20.1833, "lon": 77.6833}, "Akot": {"lat": 21.1, "lon": 77.1167},
    "Ambajogai": {"lat": 18.9667, "lon": 76.6833}, "Amalner": {"lat": 21.0333, "lon": 75.3333},
    "Anjangaon Surji": {"lat": 21.1167, "lon": 77.8667}, "Arvi": {"lat": 20.45, "lon": 78.15},
    "Ashti": {"lat": 18.0, "lon": 76.25}, "Atpadi": {"lat": 17.1667, "lon": 74.4167},
    "Baramati": {"lat": 18.15, "lon": 74.6}, "Barshi": {"lat": 18.11, "lon": 76.06},
    "Basmat": {"lat": 18.7, "lon": 77.856}, "Bhokar": {"lat": 19.5167, "lon": 77.3833},
    "Biloli": {"lat": 19.5333, "lon": 77.2167}, "Chikhli": {"lat": 20.9, "lon": 76.0167},
    "Daund": {"lat": 18.4667, "lon": 74.65}, "Deola": {"lat": 20.5667, "lon": 74.05},
    "Dhanora": {"lat": 20.7167, "lon": 79.0167}, "Dharni": {"lat": 21.25, "lon": 78.2667},
    "Dharur": {"lat": 18.0833, "lon": 76.7}, "Digras": {"lat": 19.45, "lon": 77.55},
    "Dindori": {"lat": 21.0, "lon": 79.0}, "Erandol": {"lat": 21.0167, "lon": 75.2167},
    "Faizpur": {"lat": 21.1167, "lon": 75.7167}, "Gadhinglaj": {"lat": 16.2333, "lon": 74.1333},
    "Guhagar": {"lat": 16.4, "lon": 73.4}, "Hinganghat": {"lat": 20.0167, "lon": 78.7667},
    "Igatpuri": {"lat": 19.6961, "lon": 73.5212}, "Junnar": {"lat": 19.2667, "lon": 73.8833},
    "Kankavli": {"lat": 16.3833, "lon": 73.5167}, "Koregaon": {"lat": 17.2333, "lon": 74.1167},
    "Kupwad": {"lat": 16.7667, "lon": 74.4667}, "Lonar": {"lat": 19.9833, "lon": 76.5167},
    "Mangaon": {"lat": 18.1869, "lon": 73.2555}, "Mangalwedha": {"lat": 16.6667, "lon": 75.1333},
    "Morshi": {"lat": 20.0556, "lon": 77.7647}, "Pandharpur": {"lat": 17.6658, "lon": 75.3203},
    "Parli": {"lat": 18.8778, "lon": 76.65}, "Rahuri": {"lat": 19.2833, "lon": 74.5833},
    "Raver": {"lat": 20.5876, "lon": 75.9002}, "Sangamner": {"lat": 19.3167, "lon": 74.5333},
    "Savner": {"lat": 21.0833, "lon": 79.1333}, "Sillod": {"lat": 20.0667, "lon": 75.1833},
    "Tumsar": {"lat": 20.4623, "lon": 79.5429}, "Udgir": {"lat": 18.4167, "lon": 77.1239},
    "Ulhasnagar": {"lat": 19.218451, "lon": 73.16024}, "Vasai-Virar": {"lat": 19.391003, "lon": 72.839729},
    "Wadgaon Road": {"lat": 18.52, "lon": 73.85}, "Wadwani": {"lat": 18.9, "lon": 76.69},
    "Wai": {"lat": 17.9524, "lon": 73.8775}, "Wani": {"lat": 19.0, "lon": 78.002},
    "Wardha": {"lat": 20.745445, "lon": 78.602452}, "Wardha Road": {"lat": 20.75, "lon": 78.6},
    "Yavatmal": {"lat": 20.389917, "lon": 78.130051}
}

major_cities_available = [c for c in ["Mumbai", "Pune", "Nagpur", "Thane", "Nashik", "Kalyan", "Vasai-Virar", "Aurangabad", "Solapur", "Mira-Bhayandar", "Bhiwandi", "Amravati", "Nanded", "Kolhapur", "Ulhasnagar", "Sangli", "Malegaon", "Jalgaon", "Akola", "Latur", "Dhule", "Ahmadnagar", "Chandrapur", "Parbhani", "Ichalkaranji", "Jalna", "Ambernath", "Bhusawal", "Panvel", "Dombivli"] if c in city_dict]
remaining_cities = sorted([c for c in city_dict if c not in major_cities_available])
city_options = major_cities_available + remaining_cities

# --- 데이터 로드 (공지사항 및 투어 일정) ---
tour_notices = load_json(NOTICE_FILE)
tour_schedule = load_json(CITY_FILE)
user_posts = load_json(USER_POST_FILE)


# ----------------------------------------------------------------------
# 6. 제목 및 크리스마스 UI
# ----------------------------------------------------------------------

# --- 크리스마스 테마 CSS 및 애니메이션 (추가) ---
st.markdown(
    textwrap.dedent("""
    <style>
    /* 1. '거룩한 밤' 테마: 어두운 배경 및 텍스트 색상 */
    body {
        background-color: #0d1a26; /* 매우 어두운 파란색 (밤하늘) */
        color: #f0f0f0; /* 밝은 텍스트 */
    }

    .stApp {
        background: linear-gradient(to bottom, #000000 0%, #0d1a26 15%, #1a3a52 100%);
        background-attachment: fixed;
    }

    /* 2. 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1em;
        font-weight: bold;
    }

    /* 3. 탭 버튼 오른쪽 정렬 */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: flex-end;
    }

    .stTabs [data-baseweb="tab-list"] button {
        background-color: rgba(255, 255, 255, 0.05); /* 반투명 버튼 */
        color: #f0f0f0;
        border-radius: 8px 8px 0 0;
        margin: 0 4px;
        border-bottom: 3px solid #66BB66; /* 비활성 탭 하단 라인 (그린) */
        transition: all 0.2s ease-in-out;
        padding-left: 20px; 
        padding-right: 20px;
    }

    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background-color: #BB3333; /* 활성 탭 배경 (레드) */
        color: #FFFFFF;
        border-bottom: 3px solid #FFD700; /* 활성 탭 하단 라인 (골드) */
    }

    /* 3. 버튼 스타일 */
    .stButton > button {
        background-color: transparent; 
        color: #FF8C00; 
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        border: 2px solid #FF8C00; 
        transition: all 0.2s ease-in-out;
        box-shadow: none; 
    }
    .stButton > button:hover {
        background-color: rgba(255, 140, 0, 0.1); 
        color: #FFA500; 
        border-color: #FFA500; 
        transform: translateY(-2px);
        box-shadow: none; 
    }
    
    /* 언어 선택 칸(버튼)에 포인터 커서 */
    .stSelectbox > div > div > button {
        cursor: pointer !important;
    }

    /* 4. 입력 필드 스타일 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > button,
    .stDateInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.05);
        color: #f0f0f0;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus,
    .stSelectbox > div > div > button:focus,
    .stDateInput > div > div > input:focus {
        border-color: #FFD700; /* 포커스 시 골드 */
        box-shadow: 0 0 0 0.1rem rgba(255, 215, 0, 0.25);
    }
    
    /* 5. Expander (접기/펴기) 스타일 */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.05);
        color: #f0f0f0;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.2s ease-in-out;
    }
    .streamlit-expanderHeader:hover {
        background-color: rgba(255, 255, 255, 0.1);
        color: #FFFFFF;
    }
    .streamlit-expanderContent {
        background-color: rgba(0, 0, 0, 0.1);
        border-radius: 0 0 8px 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-top: none;
    }
    
    /* 6. 제목 (h1) 네온사인 스타일 */
    .christmas-title {
        text-align: center;
        font-family: 'Mountains of Christmas', cursive; /* 구글 폰트 */
        font-size: 4.0em; /* 크기 조절 */
        font-weight: 700;
        color: #FFFFFF; /* 기본 흰색 */
        position: relative;
        z-index: 10;
        margin-bottom: 20px;
    }

    /* 1. 네온 효과 */
    .neon-effect {
        text-shadow:
            0 0 5px #fff,
            0 0 10px #fff,
            0 0 20px #BB3333;
    }
    
    /* 제목 컨테이너 (h1 내부) */
    .christmas-title-container {
        display: block;
    }

    /* 7. 크리스마스 아이콘 애니메이션 */
    .christmas-icons {
        position: relative;
        width: 80%; 
        margin: 0 auto; 
        height: 60px; 
        pointer-events: none;
        overflow: visible; 
        z-index: 10; 
    }

    .christmas-icon {
        position: absolute;
        display: block;
        font-size: 20px; 
        color: #FFFFFF;
        animation-name: bob-up-down; 
        animation-timing-function: linear;
        animation-iteration-count: infinite;
        opacity: 0.8;
    }

    @keyframes bob-up-down {
        0%  { transform: translateY(0px) rotate(-5deg); }
        50% { transform: translateY(-10px) rotate(5deg); }
        100% { transform: translateY(0px) rotate(-5deg); }
    }

    /* === Starry Sky and Pulsating Star CSS (별 배경) === */
    .star-field-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        pointer-events: none;
        overflow: hidden;
        z-index: 1; 
    }
    
    /* 베들레헴의 별 CSS */
    .bethlehem-star {
        position: fixed; 
        top: 8vh; /* 뷰포트 높이의 8% 위치로 조정 */
        left: 50px; /* 좌측 상단에 위치 */
        font-size: 35px; 
        color: #FFD700; 
        text-shadow: 0 0 15px #FFD700, 0 0 30px rgba(255, 215, 0, 0.9); 
        animation: star-glow 1.5s infinite alternate;
        z-index: 9999; 
        pointer-events: none;
    }
    @keyframes star-glow {
        0% { opacity: 0.8; transform: scale(1); }
        100% { opacity: 1.0; transform: scale(1.1); }
    }
    
    /* 눈 내리는 듯한 별 애니메이션 키프레임 */
    @keyframes star-fall {
        0% { transform: translateY(0) scale(1); opacity: 0.8; }
        100% { transform: translateY(100vh) scale(0.5); opacity: 0; }
    }

    /* 느리게 반짝이는 애니메이션 키프레임 (트리거용) */
    @keyframes twinkle-slow {
        0% { opacity: 0.1; }
        50% { opacity: 0.8; }
        100% { opacity: 0.1; }
    }
    /* === Starry Sky and Pulsating Star CSS 끝 === */
    
    /* 9. Folium 맵 스타일 */
    .st-bv { /* st_folium 컨테이너 */
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #66BB66; /* 그린 테두리 */
        box-shadow: 0 0 15px rgba(102, 187, 102, 0.4);
    }
    
    /* 10. 공지/포스트 박스 */
    .notice-content-box {
        background-color: rgba(0, 0, 0, 0.2);
        padding: 12px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 10px;
        margin-bottom: 10px;
        color: #f0f0f0;
    }
    
    /* 11. 도시 목록 사이 이동 정보 스타일 */
    .route-info {
        text-align: center; 
        margin-top: 5px; 
        margin-bottom: 10px; 
        font-size: 1.1em;
        padding: 5px;
        background-color: rgba(102, 187, 102, 0.1); /* 연한 그린 배경 */
        border-radius: 5px;
        border-left: 3px solid #66BB66;
    }
    
    /* 사용자 포스트 이미지/미디어 썸네일 스타일 */
    .user-post-media {
        max-height: 150px; 
        width: auto; 
        border-radius: 6px;
        margin-top: 10px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@400;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
    """),
    unsafe_allow_html=True
)

# --- 크리스마스 아이콘 목록 ---
christmas_icons_list = [
    "🎁", "🎄", "🔔", "🍬", "🍭", "🌟", "🕯️", "☃️"
]

# 8개 아이콘 리스트 (christmas_icons_list)와 순서대로 매칭됨
icon_styles = [
    {"left": 6, "top": 15, "duration": 4.5, "delay": 0.2, "size": 30}, 
    {"left": 20, "top": 5,  "duration": 5.0, "delay": 1.5, "size": 25}, 
    {"left": 30, "top": 20, "duration": 4.2, "delay": 1.0, "size": 28}, 
    {"left": 45, "top": 10, "duration": 5.5, "delay": 3.0, "size": 22}, 
    {"left": 65, "top": 0,  "duration": 3.5, "delay": 0.0, "size": 22}, 
    {"left": 83, "top": 15, "duration": 4.8, "delay": 1.2, "size": 28}, 
    {"left": 50, "top": 30, "duration": 5.8, "delay": 3.5, "size": 25}, 
    {"left": 70, "top": 30, "duration": 5.2, "delay": 4.0, "size": 35}, 
]

# --- 크리스마스 아이콘 생성 및 애니메이션 주입 ---
def generate_christmas_icons(): 
    icons_html = ""
    for i, icon in enumerate(christmas_icons_list):
        style = icon_styles[i]
        left = style["left"]
        top = style["top"]
        duration = style["duration"]
        delay = style["delay"]
        size = style["size"] 
        
        icons_html += textwrap.dedent(f"""
            <span class="christmas-icon" style="
                font-size: {size}px;
                left: {left}%;
                top: {top}px; 
                animation-duration: {duration}s;
                animation-delay: {delay}s;
            ">{icon}</span>
        """)
    return f'<div class="christmas-icons">{icons_html}</div>'

# === Starry Background and Big Star Functions ===
def generate_star_background(num_stars=480, twinkling_count=14): 
    stars_html = ""
    twinkling_indices = random.sample(range(num_stars), twinkling_count)
    
    for i in range(num_stars):
        left = random.randint(0, 100)
        
        normalized_y_start = random.random() ** 2 
        top_start = int(normalized_y_start * 33) 

        size = random.uniform(1.0, 3.0) * (2/3)  
        
        # 속도를 2/3으로 줄이기 위해 지속 시간을 1.5배로 늘림 (10->15, 25->37.5)
        fall_duration = random.uniform(15, 37.5) 
        fall_delay = random.uniform(0, 15) 

        is_twinkling = i in twinkling_indices
        
        # [이어서 작성할 코드] - NameError 방지 및 함수 완성
        style_attributes = f"""
            position: absolute;
            left: {left}vw;
            top: {top_start}vh;
            width: {size}px;
            height: {size}px;
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 50%;
            box-shadow: 0 0 5px rgba(255, 255, 255, 0.5);
            animation: star-fall {fall_duration}s linear infinite, 
                {'twinkle-slow ' + str(random.uniform(2.0, 5.0)) + 's infinite alternate' if is_twinkling else 'none'};
            animation-delay: {fall_delay}s;
        """
        stars_html += f'<div style="{style_attributes}"></div>'
    
    return f'<div class="star-field-container">{stars_html}</div>'
# === Starry Background and Big Star Functions 끝 ===


# --- 7. UI 구성 요소 ---

def app_header():
    """앱의 제목, 베들레헴의 별, 크리스마스 아이콘을 표시합니다."""
    # 1. 별 배경 및 베들레헴의 별 배치
    st.markdown(generate_star_background(), unsafe_allow_html=True)
    st.markdown('<span class="bethlehem-star">🌟</span>', unsafe_allow_html=True)

    # 2. 크리스마스 아이콘 애니메이션 배치
    st.markdown(generate_christmas_icons(), unsafe_allow_html=True)
    
    # 3. 제목 배치 (네온 효과 적용)
    st.markdown(f"""
        <div class="christmas-title-container">
            <h1 class="christmas-title neon-effect">
                {_("title_cantata")} <span style="font-size: 0.8em; color: #66BB66;">{_("title_year")}</span>
            </h1>
        </div>
        <h3 style='text-align: center; color: #FFD700;'>
            {_("title_region")}
        </h3>
        <hr style='border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;'>
    """, unsafe_allow_html=True)


def control_panel():
    """언어 선택 및 로그인/로그아웃 버튼을 표시합니다."""
    col_lang, col_login = st.columns([1, 1])

    with col_lang:
        # 언어 선택
        selected_lang = st.selectbox("🌐", options=list(LANG.keys()), 
                                     format_func=lambda x: {"ko": "한국어", "en": "English", "hi": "हिंदी"}.get(x, x),
                                     index=list(LANG.keys()).index(st.session_state.lang),
                                     label_visibility="collapsed",
                                     key="lang_select")
        if selected_lang != st.session_state.lang:
            st.session_state.lang = selected_lang
            st.rerun()

    with col_login:
        if st.session_state.admin:
            # 로그아웃 버튼
            if st.button(f"🚪 {_('logout')}", key="btn_logout"):
                st.session_state.admin = False
                st.session_state.logged_in_user = None
                st.session_state.show_controls = False
                st.session_state.show_login_form = False
                st.success(_("logged_out_success"))
                st.rerun()
        else:
            # 로그인 폼 표시/숨김 버튼
            if st.button(f"👤 {_('login')}", key="btn_toggle_login"):
                st.session_state.show_login_form = not st.session_state.show_login_form
                st.session_state.show_controls = False

        # 로그인 폼
        if st.session_state.show_login_form:
            with st.form(key="admin_login_form"):
                st.subheader(f"🔐 {_('admin_login')}")
                password = st.text_input("Password", type="password", label_visibility="collapsed")
                login_submitted = st.form_submit_button(_("login"))

                if login_submitted:
                    if password == ADMIN_PASS:
                        st.session_state.admin = True
                        st.session_state.logged_in_user = "Admin"
                        st.session_state.show_login_form = False
                        st.session_state.show_controls = True
                        st.success(_("logged_in_success"))
                        st.rerun() # UI 업데이트를 위해 새로고침
                    else:
                        st.error(_("incorrect_password"))


# --- 8. 공지사항 탭 구현 ---

def notice_tab():
    global tour_notices
    
    st.markdown(f"## 📢 {_('tab_notice')}")
    
    if st.session_state.admin:
        with st.expander(f"📝 {_('tour_schedule_management')} ({_('tab_notice')})", expanded=st.session_state.notice_open):
            notice_id = st.text_input("Notice ID (for update/delete)", value="", placeholder="Enter ID for edit")
            notice_title = st.text_input("Title", key="notice_title_input")
            notice_content = st.text_area(_("content"), key="notice_content_input")
            notice_type = st.selectbox(_("type"), options=["urgent", "general"], format_func=lambda x: _(x), key="notice_type_select")
            uploaded_files = st.file_uploader(_("file_attachment"), accept_multiple_files=True)
            
            col_reg, col_upd, col_rem = st.columns(3)

            with col_reg:
                if st.button(_("register"), key="btn_reg_notice"):
                    if not notice_title or not notice_content:
                        st.error(_("fill_in_fields"))
                    else:
                        new_files = save_uploaded_files(uploaded_files)
                        new_notice = {
                            "id": str(uuid.uuid4()),
                            "title": notice_title,
                            "content": notice_content,
                            "type": notice_type,
                            "timestamp": datetime.now(timezone('Asia/Seoul')).isoformat(),
                            "files": new_files
                        }
                        tour_notices.insert(0, new_notice)
                        save_json(NOTICE_FILE, tour_notices)
                        st.success(_("notice_reg_success"))
                        st.session_state.notice_open = False
                        st.rerun()

            with col_upd:
                if st.button(_("update"), key="btn_upd_notice"):
                    if notice_id and notice_title and notice_content:
                        found = False
                        for notice in tour_notices:
                            if notice['id'] == notice_id:
                                # 기존 파일 유지 및 새 파일 추가
                                existing_files = notice.get('files', [])
                                new_files = save_uploaded_files(uploaded_files)
                                notice.update({
                                    "title": notice_title,
                                    "content": notice_content,
                                    "type": notice_type,
                                    "timestamp": datetime.now(timezone('Asia/Seoul')).isoformat(),
                                    "files": existing_files + new_files
                                })
                                save_json(NOTICE_FILE, tour_notices)
                                st.success(_("notice_upd_success"))
                                found = True
                                st.session_state.notice_open = False
                                st.rerun()
                                break
                        if not found: st.error("Notice ID not found.")
                    else: st.error(_("fill_in_fields"))

            with col_rem:
                if st.button(_("remove"), key="btn_rem_notice"):
                    if notice_id:
                        tour_notices[:] = [n for n in tour_notices if n['id'] != notice_id]
                        save_json(NOTICE_FILE, tour_notices)
                        st.success(_("notice_del_success"))
                        st.session_state.notice_open = False
                        st.rerun()
                    else: st.error("Please enter Notice ID to remove.")

    st.markdown(f"### {_('existing_notices')}")
    if not tour_notices:
        st.info(_("no_notices"))
    else:
        for notice in tour_notices:
            is_urgent = notice.get('type') == 'urgent'
            icon = "🚨" if is_urgent else "ℹ️"
            header_color = "#BB3333" if is_urgent else "#FFD700" # Urgent: Red, General: Gold

            st.markdown(f"""
                <div style="
                    border: 2px solid {header_color}; 
                    border-radius: 8px; 
                    margin-bottom: 15px; 
                    padding: 10px;
                    background-color: rgba(0, 0, 0, 0.3);
                ">
                    <h4 style="color: {header_color}; margin-top: 0;">{icon} {notice.get('title', _('no_title'))} 
                    <span style="float: right; font-size: 0.7em; color: #888;">ID: {notice['id'][:8]}...</span></h4>
                    <p style="font-size: 0.9em; color: #BBB;">{_(notice.get('type', 'general').lower()).capitalize()} | 
                    {datetime.fromisoformat(notice['timestamp']).strftime('%Y-%m-%d %H:%M')}</p>
                    <div class="notice-content-box">
                        {notice.get('content', _('no_content')).replace('\n', '<br>')}
                    </div>
                    
                    <p style='margin-bottom: 0;'><strong>{_('attached_files')}:</strong></p>
            """, unsafe_allow_html=True)
            
            if notice.get('files'):
                for f_info in notice['files']:
                    display_and_download_file(f_info, notice['id'], is_admin=st.session_state.admin)
            else:
                st.markdown(f"<p style='margin-left: 10px; color: #888;'>{_('no_files')}</p>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)


# --- 9. 사용자 포스트 탭 구현 ---
def user_posts_tab():
    global user_posts
    
    st.markdown(f"## 💬 {_('user_posts')}")
    
    # 1. 포스트 작성 섹션
    with st.expander(f"✍️ {_('new_post')}", expanded=False):
        post_content = st.text_area(_("post_content"), key="new_post_content")
        media_files = st.file_uploader(_("media_attachment"), type=['jpg', 'jpeg', 'png', 'mp4', 'mov'], accept_multiple_files=True)
        
        if st.button(_("register"), key="btn_submit_post"):
            if not post_content:
                st.error("포스트 내용을 입력해주세요.")
            else:
                new_files = save_uploaded_files(media_files)
                new_post = {
                    "id": str(uuid.uuid4()),
                    "content": post_content,
                    "timestamp": datetime.now(timezone('Asia/Seoul')).isoformat(),
                    "files": new_files
                }
                user_posts.insert(0, new_post)
                save_json(USER_POST_FILE, user_posts)
                st.success(_("post_success"))
                st.rerun()

    st.markdown("---")

    # 2. 포스트 목록 표시 섹션
    if not user_posts:
        st.info(_("no_posts"))
    else:
        for post in user_posts:
            post_id = post['id']
            post_time = datetime.fromisoformat(post['timestamp']).strftime('%Y-%m-%d %H:%M')
            
            st.markdown(f"""
                <div style="
                    border: 1px solid rgba(255, 255, 255, 0.2); 
                    border-radius: 8px; 
                    margin-bottom: 15px; 
                    padding: 10px;
                    background-color: rgba(0, 0, 0, 0.3);
                ">
                    <p style="font-size: 0.9em; color: #BBB; margin-bottom: 5px;">
                        👤 Anonymous | {post_time} 
                        <span style="float: right; font-size: 0.7em; color: #888;">ID: {post_id[:8]}...</span>
                    </p>
                    <div class="notice-content-box" style="margin-top: 5px;">
                        {post.get('content', _('no_content')).replace('\n', '<br>')}
                    </div>
            """, unsafe_allow_html=True)
            
            # 첨부 파일 (관리자만 볼 수 있음)
            if post.get('files'):
                st.markdown(f"<p style='margin-bottom: 0;'><strong>{_('attached_files')}:</strong></p>", unsafe_allow_html=True)
                for f_info in post['files']:
                    display_and_download_file(f_info, post_id, is_admin=st.session_state.admin, is_user_post=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 관리자만 포스트 삭제 가능
            if st.session_state.admin:
                if st.button(f"🗑️ {_('remove')}", key=f"delete_post_{post_id}"):
                    user_posts[:] = [p for p in user_posts if p['id'] != post_id]
                    save_json(USER_POST_FILE, user_posts)
                    st.success("포스트가 삭제되었습니다.")
                    st.rerun()


# --- 10. 지도 탭 구현 (NameError FIX 포함) ---

def tour_map_tab():
    global tour_schedule

    st.markdown(f"## 🗺️ {_('tab_map')} ({_('venue_list_title')})")
    
    # 1. 관리자 데이터 입력 섹션
    if st.session_state.admin:
        with st.expander(f"📝 {_('tour_schedule_management')}", expanded=st.session_state.map_open):
            
            # 수정/삭제 ID 입력
            schedule_id = st.text_input("Schedule ID (for update/delete)", value="", placeholder="Enter ID for edit")
            
            col1, col2 = st.columns(2)
            with col1:
                input_date = st.date_input(_("date"), date.today(), key="schedule_date_input")
                input_city = st.selectbox(_("city_name"), options=city_options, key="schedule_city_select")
                input_venue = st.text_input(_("venue"), placeholder=_("venue_placeholder"), key="schedule_venue_input")
                input_type = st.selectbox(_("type"), options=["indoor", "outdoor", "no_show"], format_func=lambda x: _(x), key="schedule_type_select")
            with col2:
                input_seats = st.number_input(_("seats"), min_value=0, value=500, help=_("seats_tooltip"), key="schedule_seats_input")
                input_probability = st.slider(_("probability"), min_value=0, max_value=100, value=100, step=5, key="schedule_prob_input")
                input_link = st.text_input(_("google_link"), placeholder=_("google_link_placeholder"), key="schedule_link_input")
                input_note = st.text_area(_("note"), placeholder=_("note_placeholder"), key="schedule_note_input")

            
            col_reg, col_upd, col_rem = st.columns(3)
            
            # 등록 함수
            def register_schedule():
                if not input_city or not input_venue:
                    st.error(_("warning"))
                    return
                if input_city not in city_dict:
                    st.error(_("city_coords_error"))
                    return
                    
                new_item = {
                    "id": str(uuid.uuid4()),
                    "date": input_date.isoformat(),
                    "city": input_city,
                    "venue": input_venue,
                    "type": input_type,
                    "seats": input_seats,
                    "probability": input_probability,
                    "link": input_link,
                    "note": input_note,
                    "lat": city_dict[input_city]['lat'],
                    "lon": city_dict[input_city]['lon']
                }
                tour_schedule.append(new_item)
                # 날짜 순으로 정렬 후 저장
                tour_schedule.sort(key=lambda x: (x['date'], x['city']))
                save_json(CITY_FILE, tour_schedule)
                st.success(_("schedule_reg_success"))
                st.session_state.map_open = False
                st.rerun()

            # 수정 함수
            def update_schedule():
                if not schedule_id:
                    st.error("수정할 ID를 입력하세요.")
                    return
                if input_city not in city_dict:
                    st.error(_("city_coords_error"))
                    return

                found = False
                for item in tour_schedule:
                    if item['id'] == schedule_id:
                        item.update({
                            "date": input_date.isoformat(),
                            "city": input_city,
                            "venue": input_venue,
                            "type": input_type,
                            "seats": input_seats,
                            "probability": input_probability,
                            "link": input_link,
                            "note": input_note,
                            "lat": city_dict[input_city]['lat'],
                            "lon": city_dict[input_city]['lon']
                        })
                        found = True
                        break
                
                if found:
                    tour_schedule.sort(key=lambda x: (x['date'], x['city']))
                    save_json(CITY_FILE, tour_schedule)
                    st.success(_("schedule_upd_success"))
                    st.session_state.map_open = False
                    st.rerun()
                else:
                    st.error("Schedule ID not found.")

            # 제거 함수
            def remove_schedule():
                if not schedule_id:
                    st.error("제거할 ID를 입력하세요.")
                    return
                
                initial_len = len(tour_schedule)
                tour_schedule[:] = [item for item in tour_schedule if item['id'] != schedule_id]
                
                if len(tour_schedule) < initial_len:
                    save_json(CITY_FILE, tour_schedule)
                    st.success(_("schedule_del_success"))
                    st.session_state.map_open = False
                    st.rerun()
                else:
                    st.error("Schedule ID not found.")


            with col_reg: st.button(_("register"), key="btn_reg_schedule", on_click=register_schedule)
            with col_upd: st.button(_("update"), key="btn_upd_schedule", on_click=update_schedule)
            with col_rem: st.button(_("remove"), key="btn_rem_schedule", on_click=remove_schedule)
            
            # 전체 데이터 영구 삭제 (관리자용)
            st.markdown("---")
            with st.expander(f"⚠️ {_('delete_all_data')}"):
                st.warning(_("delete_all_warning"))
                delete_pass = st.text_input("Enter Admin Password to confirm permanent deletion", type="password", key="delete_all_pass")
                if st.button(_("delete_all_confirm"), key="btn_delete_all", type="primary"):
                    if delete_pass == ADMIN_PASS:
                        try:
                            os.remove(NOTICE_FILE)
                            os.remove(CITY_FILE)
                            os.remove(USER_POST_FILE)
                            # 파일 내의 실제 첨부 파일도 삭제 (옵션)
                            for f in os.listdir(UPLOAD_DIR):
                                os.remove(os.path.join(UPLOAD_DIR, f))
                            
                            st.session_state.admin = False
                            st.session_state.logged_in_user = None
                            st.success(_("delete_all_success"))
                            st.rerun()
                        except Exception as e:
                            st.error(f"데이터 삭제 중 오류가 발생했습니다: {e}")
                    else:
                        st.error(_("incorrect_password"))


    # 2. 지도 표시 섹션
    if not tour_schedule:
        st.info(_("no_schedule"))
        return

    # Map 초기화 (평균 좌표: 18.5204, 73.8567 - Pune 근처)
    m = folium.Map(location=[19.5, 75.0], zoom_start=7, tiles="cartodbdarkmatter")
    
    # 경로 좌표 리스트
    route_coords = []
    
    # 랜드마크 (예: 뭄바이)
    if "Mumbai" in city_dict:
        mumbai_coords = (city_dict['Mumbai']['lat'], city_dict['Mumbai']['lon'])
        folium.Marker(
            mumbai_coords,
            icon=folium.Icon(color='red', icon='flag', prefix='fa'),
            popup=f"<b>Mumbai</b><br>Tour Starting Point"
        ).add_to(m)
        
    # 일정 마커 추가
    prev_coords = None
    for i, item in enumerate(tour_schedule):
        
        # --- NameError FIX: 유형별 아이콘 및 색상 정의 ---
        # item이 정의된 직후에 이 변수들을 정의해야 NameError를 방지할 수 있습니다.
        type_key = item.get('type', 'indoor')

        if type_key == 'indoor':
            translated_type = _('indoor')
            type_color_html = '#FFD700'  # Gold
            map_type_icon_fa = 'fa-building-o'
            icon_color = 'orange'
        elif type_key == 'outdoor':
            translated_type = _('outdoor')
            type_color_html = '#66BB66' # Green
            map_type_icon_fa = 'fa-tree'
            icon_color = 'green'
        elif type_key == 'no_show':
            translated_type = _('no_show')
            type_color_html = '#AAAAAA' # Gray
            map_type_icon_fa = 'fa-ban'
            icon_color = 'lightgray'
        else:
            translated_type = _('general')
            type_color_html = '#FFFFFF' # White
            map_type_icon_fa = 'fa-star'
            icon_color = 'white'
        # --- NameError FIX 끝 ---

        lat, lon = item.get('lat'), item.get('lon')
        if lat is None or lon is None:
            continue
            
        current_coords = (lat, lon)
        route_coords.append(current_coords)
        
        # 구글맵 링크 처리
        link_url = item.get('link', '')
        if link_url and not link_url.startswith(('http', 'https')):
            link_url = f"https://www.google.com/maps/search/?api=1&query={quote(link_url)}"
        elif not link_url:
            link_url = f"https://www.google.com/maps/search/?api=1&query={quote(item['city'])} {quote(item['venue'])}"

        # 팝업 HTML (Traceback 라인 1375에서 map_type_icon_fa가 필요했음)
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; color: #333; max-width: 300px;">
            <h4 style="color: #BB3333; margin-top: 0;">{item['city']} ({item['date']})</h4>
            <b>{_('venue')}:</b> {item['venue']}<br>
            <b>{_('type')}:</b> <span style="color: {type_color_html};"><i class="fa {map_type_icon_fa}" style="margin-right: 5px;"></i> {translated_type}</span><br>
            <b>{_('seats')}:</b> {item['seats']} / {_('probability')}: {item['probability']}%<br>
            <b>{_('note')}:</b> {item['note'] or '-'}<br>
            <a href="{link_url}" target="_blank" style="color: #66BB66; font-weight: bold;">{_('google_link')} <i class="fa fa-external-link"></i></a>
            {"<br><span style='font-size: 0.8em; color: #888;'>ID: " + item['id'][:8] + "...</span>" if st.session_state.admin else ""}
        </div>
        """
        
        # 마커 색상: 확률에 따라 조정 (100%: 주황, 50% 미만: 회색)
        marker_color = 'orange'
        if item['probability'] < 50:
            marker_color = 'gray'
        elif item['type'] == 'outdoor':
            marker_color = 'green'
        
        # Folium 마커 추가
        folium.Marker(
            current_coords,
            icon=folium.Icon(color=marker_color, icon=map_type_icon_fa, prefix='fa'),
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"{item['date']} - {item['city']}: {item['venue']} ({item['probability']}%)"
        ).add_to(m)
        
        # 경로 표시 및 거리 계산
        if prev_coords:
            distance_info = calculate_distance_and_time(prev_coords, current_coords)
            
            # 경로 팝업 HTML
            route_popup = f"""
            <div style="font-family: Arial, sans-serif; color: #333;">
                <b>{prev_city} → {item['city']}</b><br>
                거리 / 예상 시간: <b>{distance_info}</b>
            </div>
            """
            
            # AntPath로 경로 그리기 (점선)
            AntPath(
                [prev_coords, current_coords],
                color='#66BB66', # 그린
                weight=3,
                opacity=0.8,
                delay=800,
                dash_array='5, 10', # 점선
                popup=folium.Popup(route_popup, max_width=200)
            ).add_to(m)

        # 다음 반복을 위해 현재 도시 정보 저장
        prev_coords = current_coords
        prev_city = item['city']
        
    # 3. 지도 출력
    st_folium(m, width=700, height=500, key="tour_map")
    st.markdown(f"<p style='text-align: center; color: #bbb;'>{_('caption')}</p>", unsafe_allow_html=True)
    
    # 4. 일정 목록 표시
    st.markdown("---")
    st.markdown(f"### {_('venue_list_title')}")
    
    # 날짜별 그룹화
    schedule_by_date = {}
    for item in tour_schedule:
        date_str = item['date']
        if date_str not in schedule_by_date:
            schedule_by_date[date_str] = []
        schedule_by_date[date_str].append(item)

    # 정렬된 날짜 순서로 표시
    sorted_dates = sorted(schedule_by_date.keys())
    
    prev_coords_list = []
    
    for date_str in sorted_dates:
        st.markdown(f"#### 📅 {date_str}")
        
        for item in schedule_by_date[date_str]:
            
            # 유형별 색상 및 아이콘 재정의 (일관성 유지)
            type_key = item.get('type', 'indoor')
            if type_key == 'indoor': icon, color = "🏢", "#FFD700"
            elif type_key == 'outdoor': icon, color = "🌲", "#66BB66"
            elif type_key == 'no_show': icon, color = "🚫", "#AAAAAA"
            else: icon, color = "✨", "#FFFFFF"
            
            # 도시별 마커 표시
            col_icon, col_content, col_admin = st.columns([0.5, 4, 1])
            
            with col_icon:
                st.markdown(f"<div style='font-size: 2em; color: {color}; text-align: center; margin-top: 5px;'>{icon}</div>", unsafe_allow_html=True)

            with col_content:
                prob_style = f"color: {'#66BB66' if item['probability'] == 100 else '#BB3333'}"
                st.markdown(f"""
                    **{item['city']}** - {item['venue']}
                    <br><span style='font-size: 0.9em;'>{_(item['type'])} | {_('seats')}: {item['seats']} | 
                    <span style='{prob_style}'>{_('probability')}: {item['probability']}%</span></span>
                    <br><span style='font-size: 0.8em; color: #BBB;'>{_('note')}: {item['note'] or '-'}</span>
                """, unsafe_allow_html=True)
            
            with col_admin:
                if st.session_state.admin:
                    if st.button("Edit", key=f"edit_schedule_{item['id']}"):
                        st.session_state.map_open = True
                        st.text_input("Schedule ID (for update/delete)", value=item['id'], key="schedule_id_preload", label_visibility="collapsed")
                        st.experimental_rerun()
            
            current_list_coords = (item.get('lat'), item.get('lon'))
            if current_list_coords and prev_coords_list:
                distance_info = calculate_distance_and_time(prev_coords_list[-1], current_list_coords)
                st.markdown(f"<div class='route-info'>➡️ 🚌 {distance_info}</div>", unsafe_allow_html=True)
            
            if current_list_coords:
                 prev_coords_list.append(current_list_coords)


# --- 11. 메인 앱 로직 ---

if __name__ == "__main__":
    
    # 1. 헤더 및 컨트롤 패널 표시
    app_header()
    control_panel()
    
    # 2. 탭 구성
    # "공지", "칸타타 투어", "사용자 포스트" 탭 추가
    tab_notice, tab_map, tab_posts = st.tabs([f"📢 {_('tab_notice')}", f"🗺️ {_('tab_map')}", f"💬 {_('user_posts')}"])

    with tab_notice:
        # 공지사항 탭 로직 호출 (CRUD 및 표시)
        notice_tab()

    with tab_map:
        # 지도/일정 탭 로직 호출 (NameError FIX 포함)
        tour_map_tab()
        
    with tab_posts:
        # 사용자 포스트 탭 로직 호출
        user_posts_tab()

    # 3. 디버깅 정보 (옵션)
    if st.session_state.admin:
        with st.expander("Admin Debug Info"):
            st.write(st.session_state)
            st.write("Tour Schedule (First 3):", tour_schedule[:3])
            st.write("Notices (First 3):", tour_notices[:3])
            st.write("User Posts (First 3):", user_posts[:3])
