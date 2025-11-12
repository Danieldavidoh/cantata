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
import textwrap # <<< 수정: 들여쓰기 문제 해결을 위해 import

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
        "tab_notice": "공지", "tab_map": "칸타타 투어", "indoor": "실내", "outdoor": "실외", 
        "venue": "공연 장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵",
        "warning": "도시와 장소를 입력하세요", "delete": "제거", "menu": "메뉴", "login": "로그인", "logout": "로그아웃",
        "add_city": "추가", "register": "등록", "update": "수정", "remove": "제거",
        "date": "날짜", "city_name": "도시 이름", "search_placeholder": "도시/장소 검색...",
        "general": "일반", "urgent": "긴급", "admin_login": "관리자 로그인", "update_content": "내용 수정",
        "existing_notices": "기존 공지사항", "no_notices": "공지사항이 없습니다.", "content": "내용",
        "no_content": "내용 없음", "no_title": "제목 없음", 
        "tour_schedule_management": "공연도시 정보 입력", 
        "venue_list_title": "공연 도시 목록", 
        "set_data": "데이터 설정", "type": "유형", "city": "도시", "link": "링크", "past_route": "지난 경로",
        "single_location": "단일 위치", "legend": "범례", "no_schedule": "일정이 없습니다.",
        "city_coords_error": "좌표를 찾을 수 없습니다. city_dict에 추가해 주세요.",
        "logged_in_success": "관리자로 로그인했습니다.", "logged_out_success": "로그아웃했습니다.",
        "incorrect_password": "비밀번호가 틀렸습니다.", "fill_in_fields": "제목과 내용을 채워주세요.",
        "notice_reg_success": "공지사항이 성공적으로 등록되었습니다!", "notice_del_success": "공지사항이 삭제되었습니다.",
        "notice_upd_success": "공지사항이 수정되었습니다.", "schedule_reg_success": "일정이 등록되었습니다.",
        "schedule_del_success": "일정 항목이 제거되었습니다.", "schedule_upd_success": "일정이 성공적으로 수정되었습니다.",
        "venue_placeholder": "공연 장소를 입력하세요", "note_placeholder": "특이사항을 입력하세요",
        "google_link_placeholder": "장소 이름(예: Dagdusheth Halwai Ganpati) 또는 URL", 
        "seats_tooltip": "예상 관객 인원",
        "file_attachment": "파일 첨부", "attached_files": "첨부 파일", "no_files": "없음",
        "user_posts": "사용자 포스트",
        "new_post": "새 포스트 작성",
        "post_content": "포스트 내용",
        "media_attachment": "사진/동영상 첨부",
        "post_success": "포스트가 성공적으로 업로드되었습니다!",
        "no_posts": "현재 포스트가 없습니다.",
        "admin_only_files": "첨부 파일은 관리자만 확인 가능합니다.", # 이 키는 이제 관리자 뷰에서만 사용됨
        "probability": "가능성",
        "caption": "지도 위의 아이콘이나 경로를 클릭하여 세부 정보를 확인하세요."
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
        "seats_tooltip": "Expected audience count", "file_attachment": "File Attachment", "attached_files": "Attached Files",
        "no_files": "None", "user_posts": "User Posts", "new_post": "Create New Post", "post_content": "Post Content",
        "media_attachment": "Attach Photo/Video", "post_success": "Post uploaded successfully!", "no_posts": "No posts available.",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "Probability",
        "caption": "Click icons or routes on the map for details."
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
        "media_attachment": "फोटो/वीडियो संलग्न करें", "post_success": "पोस्ट सफलतापूर्वक अपलोड हुई!", "no_posts": "कोई पोस्ट उपलब्ध नहीं है।",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "संभावना",
        "caption": "विवरण के लिए मानचित्र पर आइकन या मार्गों पर क्लिक करें।"
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False}
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
def display_and_download_file(file_info, notice_id, is_admin=False, is_user_post=False):
    file_size_kb = round(file_info['size'] / 1024, 1)
    file_type = file_info['type']; file_path = file_info['path']; file_name = file_info['name']
    key_prefix = "admin" if is_admin else "user"

    # === 수정된 부분: 관리자 모드에서는 포스트 삭제 버튼이 따로 있으므로, "관리자만..." 메시지 표시 안함 ===
    if is_user_post and not is_admin and not os.path.exists(file_path):
         st.markdown(f"**{file_name}** (파일을 찾을 수 없습니다.)")
         return
    # === 수정 끝 ===

    if os.path.exists(file_path):
        if file_type.startswith('image/'):
            base64_data = get_file_as_base64(file_path)
            if base64_data:
                # === 수정: use_column_width=True -> use_container_width=True (경고 메시지 제거) ===
                st.image(f"data:{file_type};base64,{base64_data}", caption=f"🖼️ {file_name} ({file_size_kb} KB)", use_container_width=True)
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
                    st.download_button(label=f"⬇️ {icon} {file_name} ({file_size_kb} KB)", data=f.read(), file_name=file_name, mime=file_type, key=f"downloader_{key_prefix}_{notice_id}_{file_name}")
            except Exception:
                pass
    else:
        # 파일이 존재하지 않는 경우 메시지 표시
        if is_admin or not is_user_post: # 관리자거나, 공지사항인 경우 항상 메시지 표시
             st.markdown(f"**{file_name}** (파일을 찾을 수 없습니다.)")
        # (일반 사용자의 사용자 포스트인 경우, 파일 없으면 아무것도 표시 안함 - 위에서 처리)


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
    """두 좌표 사이의 거리와 예상 소요 시간을 문자열로 반환합니다. (320 km / 5.5h 형식)"""
    lat1, lon1 = p1
    lat2, lon2 = p2
    distance_km = haversine(lat1, lon1, lat2, lon2)

    avg_speed_kmh = 60 if distance_km < 500 else 80

    travel_time_h = distance_km / avg_speed_kmh

    # 거리와 시간 포맷 변경 (km / X.Xh)
    distance_str = f"{distance_km:.0f} km" # 소수점 없이 km
    time_str = f"{travel_time_h:.1f}h"     # 소수점 한 자리까지 h

    return f"{distance_str} / {time_str}"

# --- 5. 도시 목록 및 좌표 정의 ---
city_dict = {
    "Ahmadnagar": {"lat": 19.095193, "lon": 74.749596}, "Akola": {"lat": 20.702269, "lon": 77.004699},
    "Ambernath": {"lat": 19.186354, "lon": 73.191948}, "Amravati": {"lat": 20.93743, "lon": 77.779271},
    "Aurangabad": {"lat": 19.876165, "lon": 75.343314}, "Badlapur": {"lat": 19.1088, "lon": 73.1311},
    "Bhandara": {"lat": 21.180052, "lon": 79.564987}, "Bhiwandi": {"lat": 19.300282, "lon": 73.069645},
    "Bhusawal": {"lat": 21.02606, "lon": 75.830095}, "Chandrapur": {"lat": 19.957275, "lon": 79.296875},
    "Chiplun": {"lat": 17.5322, "lon": 73.516}, "Dhule": {"lat": 20.904964, "lon": 74.774651},
    "Dombivli": {"lat": 19.2183, "lon": 73.0865}, "Gondia": {"lat": 21.4598, "lon": 80.195},
    "Hingoli": {"lat": 19.7146, "lon": 77.1424}, "Ichalkaranji": {"lat": 16.6956, "lon": 74.4561},
    "Jalgaon": {"lat": 21.007542, "lon": 75.562554}, "Jalna": {"lat": 19.833333, "lon": 75.883333},
    "Kalyan": {"lat": 19.240283, "lon": 73.13073}, "Karad": {"lat": 17.284, "lon": 74.1779},
    "Karanja": {"lat": 20.7083, "lon": 76.93}, "Karanja Lad": {"lat": 20.3969, "lon": 76.8908},
    "Karjat": {"lat": 18.9121, "lon": 73.3259}, "Kavathe Mahankal": {"lat": 17.218, "lon": 74.416},
    "Khamgaon": {"lat": 20.691, "lon": 76.6886}, "Khopoli": {"lat": 18.6958, "lon": 73.3207},
    "Kolad": {"lat": 18.5132, "lon": 73.2166}, "Kolhapur": {"lat": 16.691031, "lon": 74.229523},
    "Kopargaon": {"lat": 19.883333, "lon": 74.483333}, "Koparkhairane": {"lat": 19.0873, "lon": 72.9856},
    "Kothrud": {"lat": 18.507399, "lon": 73.807648}, "Kudal": {"lat": 16.033333, "lon": 73.683333},
    "Kurla": {"lat": 19.0667, "lon": 72.8833}, "Latur": {"lat": 18.406526, "lon": 76.560229},
    "Lonavala": {"lat": 18.75, "lon": 73.4}, "Mahad": {"lat": 18.086, "lon": 73.3006},
    "Malegaon": {"lat": 20.555256, "lon": 74.525539}, "Malkapur": {"lat": 20.4536, "lon": 76.3886},
    "Manmad": {"lat": 20.3333, "lon": 74.4333}, "Mira-Bhayandar": {"lat": 19.271112, "lon": 72.854094},
    "Mumbai": {"lat": 19.07609, "lon": 72.877426}, "Nagpur": {"lat": 21.1458, "lon": 79.088154},
    "Nanded": {"lat": 19.148733, "lon": 77.321011}, "Nandurbar": {"lat": 21.317, "lon": 74.02},
    "Nashik": {"lat": 20.011645, "lon": 73.790332}, "Niphad": {"lat": 20.074, "lon": 73.834},
    "Osmanabad": {"lat": 18.169111, "lon": 76.035309}, "Palghar": {"lat": 19.691644, "lon": 72.768478},
    "Panaji": {"lat": 15.4909, "lon": 73.8278}, "Panvel": {"lat": 18.989746, "lon": 73.117069},
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


# --- 관리자 및 UI 설정 ---
ADMIN_PASS = "0009"

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
        background: linear-gradient(to bottom, #0d1a26 0%, #1a3a52 100%);
        background-attachment: fixed;
    }

    /* 2. 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1em;
        font-weight: bold;
    }

    /* === 3. 수정: 탭 버튼 오른쪽 정렬 === */
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
        /* === 4. 수정: 좌우 여백 추가 === */
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

    /* === 3. 수정: 버튼 스타일 (테두리) === */
    .stButton > button {
        background-color: transparent; /* 수정: 배경 투명 */
        color: #BB3333; /* 수정: 텍스트 빨간색 */
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: bold;
        border: 2px solid #BB3333; /* 수정: 빨간 테두리 */
        transition: all 0.2s ease-in-out;
        box-shadow: none; /* 수정: 그림자 제거 */
    }
    .stButton > button:hover {
        background-color: rgba(187, 51, 51, 0.1); /* 수정: 옅은 빨간 배경 */
        color: #D44444;
        border-color: #D44444;
        transform: translateY(-2px);
        box-shadow: none; /* 수정: 그림자 제거 */
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
        font-family: 'Mountains of Christmas', cursive; /* 구글 폰트 (느낌있는 폰트) */
        font-size: 4.0em; /* 크기 조절 */
        font-weight: 700;
        color: #FFFFFF; /* 기본 흰색 */
        position: relative;
        z-index: 10;
        margin-bottom: 20px;
        /* === 1. 수정: 네온사인 효과 제거 (기본값) === */
    }

    /* === 1. 수정: 네온 효과를 위한 새 클래스 === */
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

    /* === 7. 크리스마스 아이콘 애니메이션 (수정) === */
    .christmas-icons {
        position: relative; /* 수정: fixed -> relative (h1 내부) */
        width: 80%; /* 수정: 60vw -> 80% (h1 기준) */
        margin: 0 auto; /* 추가: 중앙 정렬 */
        height: 60px; /* 수정: 100px -> 60px (텍스트 상단 공간) */
        pointer-events: none;
        overflow: visible; /* 수정: hidden -> visible (아이콘 위아래로 움직일 공간) */
        z-index: 10; /* 수정: 999 -> 10 */
    }

    .christmas-icon {
        position: absolute;
        display: block;
        font-size: 20px; /* 기본 크기 */
        color: #FFFFFF;
        animation-name: bob-up-down; /* 수정: 위아래로 밥(bob)하는 애니메이션 */
        animation-timing-function: linear;
        animation-iteration-count: infinite;
        opacity: 0.8;
    }

    @keyframes bob-up-down {
        0%   { transform: translateY(0px) rotate(-5deg); }
        50%  { transform: translateY(-10px) rotate(5deg); }
        100% { transform: translateY(0px) rotate(-5deg); }
    }
    /* === 수정 끝 === */


    /* === 8. 눈 결정체 애니메이션 (복원 및 수정) === */
    .snowflakes {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        pointer-events: none;
        z-index: 998; /* 아이콘보다 아래 */
    }
    
    .snowflake {
        position: absolute;
        /* === 2. 수정: 투명도를 5% (0.05)로 설정 === */
        color: rgba(255, 255, 255, 0.05);
        font-size: 1em;
        opacity: 0;
        animation-name: fall;
        animation-timing-function: linear;
        animation-iteration-count: infinite;
    }

    @keyframes fall {
        0% { transform: translateY(-10vh) translateX(0vw); opacity: 0; }
        10% { opacity: 0.9; } /* 나타나기 시작 */
        90% { opacity: 0.9; } /* 사라지기 직전 */
        100% { transform: translateY(100vh) translateX(5vw); opacity: 0; }
    }
    /* === 수정 끝 === */
    
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
    
    /* === 11. 수정: 메뉴/로그인 숨기기 (화면 왼쪽 밖) === */
    .hidden-controls {
        position: absolute;
        left: -9999px; /* 화면 왼쪽 밖으로 이동 */
        width: 1px;
        height: 1px;
        overflow: hidden; /* 보이지 않게 */
        
        /* === 2. 수정: 공간 제거를 위한 추가 스타일 === */
        padding: 0 !important;
        margin: 0 !important;
        height: 0;
        border: none;
    }
    
    /* === 2. 수정: 숨겨진 컨트롤을 감싸는 Streamlit의 부모 컨테이너도 숨김 === */
    /* Streamlit v1.30+ */
    [data-testid="stVerticalBlock"]:has(div.hidden-controls) {
        height: 0;
        min-height: 0;
        padding: 0 !important;
        margin: 0 !important;
    }
    </style>
    
    <link href="https://fonts.googleapis.com/css2?family=Mountains+of+Christmas:wght@400;700&display=swap" rel="stylesheet">
    """),
    unsafe_allow_html=True
)
# === 수정 끝 ===

# --- 크리스마스 아이콘 목록 ---
# === 수정: 4개 아이콘(🎅, 🦌, ❄️, 🧦) 제거 ===
christmas_icons_list = [
    "🎁", "🎄", "🔔", "🍬", "🍭", "🌟", "🕯️", "☃️"
]

# === 3. 수정: 아이콘 스타일 (겹침 수정) ===
# 8개 아이콘 리스트 (christmas_icons_list)와 순서대로 매칭됨
icon_styles = [
    {"left": 12, "top": 15, "duration": 4.5, "delay": 0.2, "size": 30}, # 🎁
    {"left": 20, "top": 5,  "duration": 5.0, "delay": 1.5, "size": 25}, # 🎄
    {"left": 30, "top": 20, "duration": 4.2, "delay": 1.0, "size": 28}, # 🔔
    {"left": 45, "top": 10, "duration": 5.5, "delay": 3.0, "size": 22}, # 🍬 (50% -> 45%)
    {"left": 65, "top": 0,  "duration": 3.5, "delay": 0.0, "size": 22}, # 🍭
    {"left": 83, "top": 15, "duration": 4.8, "delay": 1.2, "size": 28}, # 🌟 (80% -> 83%)
    {"left": 50, "top": 30, "duration": 5.8, "delay": 3.5, "size": 25}, # 🕯️ (48% -> 50%)
    {"left": 70, "top": 30, "duration": 5.2, "delay": 4.0, "size": 35}, # ☃️
]
# === 수정 끝 ===

# --- 크리스마스 아이콘 생성 및 애니메이션 주입 (수정) ---
def generate_christmas_icons(): # num_icons 제거
    icons_html = ""
    # === 수정: 8개 고유 아이콘 리스트와 스타일 리스트를 함께 순회 ===
    for i, icon in enumerate(christmas_icons_list):
        # 고정된 스타일 값 가져오기
        style = icon_styles[i]
        left = style["left"]
        top = style["top"]
        duration = style["duration"]
        delay = style["delay"]
        size = style["size"] # size 가져오기
        
        # === 수정: 모든 랜덤 값 제거 ===
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

# === 8. 눈 결정체 생성 (CSS 기반) (복원) ===
def generate_snowflakes(num_flakes=25): # === 2. 수정: 밀도 조절 (56 -> 25) ===
    snowflakes_html = ""
    for _ in range(num_flakes):
        size = random.uniform(0.5, 1.2) # 눈 결정체 크기 (em)
        left = random.randint(0, 100) # % 위치
        duration = random.uniform(10, 30) # 떨어지는 시간 (느리게)
        delay = random.uniform(0, 20) # 애니메이션 시작 지연

        # === 수정된 부분: textwrap.dedent() 적용 ===
        snowflakes_html += textwrap.dedent(f"""
            <div class="snowflake" style="
                font-size: {size}em;
                left: {left}vw;
                animation-duration: {duration}s;
                animation-delay: {delay}s;
                animation-name: fall;
            ">❄</div>
        """)
        # === 수정 끝 ===
    return f'<div class="snowflakes">{snowflakes_html}</div>'

# --- 제목 렌더링 ---
# === 수정: 아이콘 HTML을 먼저 생성 ===
icons_html_str = generate_christmas_icons()
# === 수정: 눈송이 생성 함수 다시 호출 ===
st.markdown(generate_snowflakes(), unsafe_allow_html=True)

title_cantata = _('title_cantata')
title_year = _('title_year')
title_region = _('title_region')

# === 1. 수정: 네온 효과를 '칸타타 투어'와 '2025'에 적용 ===
title_html = textwrap.dedent(f"""
    <div class="christmas-title-container">
        <span class="neon-effect" style="color: #BB3333; margin-right: 10px;">{title_cantata}</span>
        <span class="neon-effect" style="color: #FFFFFF; margin-right: 10px;">{title_year}</span>
        <span style="color: #66BB66; font-size: 0.66em;">{title_region}</span>
    </div>
""")
# === 수정 끝 ===
# === 수정: h1 태그 내부에 아이콘(icons_html_str)을 먼저 삽입하여 그룹화 ===
st.markdown(f'<h1 class="christmas-title">{icons_html_str}{title_html}</h1>', unsafe_allow_html=True)


# --- 4. 수정: 컨트롤 숨기기 및 공간 제거 (구조 변경) ---

# 4a. 언어 선택 (항상 숨김)
st.markdown('<div class="hidden-controls">', unsafe_allow_html=True)
LANG_OPTIONS = {"ko": "한국어", "en": "English", "hi": "हिन्दी"}
lang_keys = list(LANG_OPTIONS.keys())
lang_display_names = list(LANG_OPTIONS.values())
current_lang_index = lang_keys.index(st.session_state.lang)
selected_lang_display = st.selectbox(
    "language", # "language"로 고정
    options=lang_display_names,
    index=current_lang_index,
    key="lang_select"
)
selected_lang_key = lang_keys[lang_display_names.index(selected_lang_display)]
if selected_lang_key != st.session_state.lang:
    st.session_state.lang = selected_lang_key
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 4b. 로그인/로그아웃 버튼 (항상 숨김)
st.markdown('<div class="hidden-controls">', unsafe_allow_html=True)
if st.session_state.admin:
    if st.button(_("logout"), key="logout_btn_hidden"):
        st.session_state.admin = False
        st.session_state.logged_in_user = None
        st.session_state.show_login_form = False
        safe_rerun()
else:
    if st.button(_("login"), key="login_btn_hidden"): 
        handle_login_button_click()
st.markdown('</div>', unsafe_allow_html=True)

# --- 로그인 / 로그아웃 로직 (핸들러) ---
def safe_rerun():
    if hasattr(st, 'rerun'): st.rerun()

def handle_login_button_click():
    st.session_state.show_login_form = not st.session_state.show_login_form
    safe_rerun()

# 4c. 로그인 폼 (조건부로 *보이게* 표시, 공간 차지)
if st.session_state.show_login_form and not st.session_state.admin:
    # 폼이 나타날 때만 col_auth를 생성하여 공간을 차지하게 함
    _, col_form = st.columns([1, 3]) # [1, 3] 비율 유지
    with col_form:
        with st.form("login_form_permanent", clear_on_submit=False):
            st.write(_("admin_login"))
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(_("login"))

            if submitted:
                if password == ADMIN_PASS:
                    st.session_state.admin = True
                    st.session_state.logged_in_user = "Admin"
                    st.session_state.show_login_form = False
                    safe_rerun()
                else: st.warning(_("incorrect_password"))
# --- 4. 수정 끝 ---


# --- 탭 구성 (수정: 아이콘 및 공백 추가) ---
tab_notice, tab_map = st.tabs([f"📢  {_('tab_notice')}", f"🚌  {_('tab_map')}"])

# =============================================================================
# 탭 1: 공지사항 (Notice)
# =============================================================================
with tab_notice:

    # 1. 관리자 공지사항 관리
    if st.session_state.admin:
        # === 5. 수정: 관리자 제목 변경 ===
        st.subheader(f"🔔 공지 관리") 

        # --- 관리자: 공지사항 등록/수정 폼 ---
        with st.expander(_("register"), expanded=False): 
            with st.form("notice_form", clear_on_submit=True):
                notice_title = st.text_input("제목")
                notice_content = st.text_area(_("note"))

                uploaded_files = st.file_uploader(
                    _("file_attachment"),
                    type=["png", "jpg", "jpeg", "pdf", "txt", "zip"],
                    accept_multiple_files=True,
                    key="notice_file_uploader"
                )

                type_options = {"General": _("general"), "Urgent": _("urgent")}
                selected_display_type = st.radio(_("type"), list(type_options.values()))
                notice_type = list(type_options.keys())[list(type_options.values()).index(selected_display_type)]

                submitted = st.form_submit_button(_("register"))

                if submitted and notice_title and notice_content:
                    file_info_list = save_uploaded_files(uploaded_files)

                    new_notice = {"id": str(uuid.uuid4()), "title": notice_title, "content": notice_content, "type": notice_type, "files": file_info_list, "date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")}
                    tour_notices.insert(0, new_notice); save_json(NOTICE_FILE, tour_notices); st.success(_("notice_reg_success")); safe_rerun()
                elif submitted: st.warning(_("fill_in_fields"))

        # --- 관리자: 공지사항 목록 및 수정/삭제 ---
        valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('id') and n.get('title')]
        notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
        type_options_rev = {"General": _("general"), "Urgent": _("urgent")}

        for notice in notices_to_display:
            notice_id = notice['id']; notice_type_key = notice.get('type', 'General')
            translated_type = type_options_rev.get(notice_type_key, _("general")); notice_title = notice['title']

            prefix = "🚨 " if notice_type_key == "Urgent" else ""
            header_text = f"{prefix}[{translated_type}] {notice_title} ({notice.get('date', 'N/A')[:10]})"

            with st.expander(header_text, expanded=False): 
                col_del, col_title = st.columns([1, 4])
                with col_del:
                    if st.button(_("remove"), key=f"del_n_{notice_id}", help=_("remove")):
                        for file_info in notice.get('files', []):
                            if os.path.exists(file_info['path']): os.remove(file_info['path'])

                        tour_notices[:] = [n for n in tour_notices if n.get('id') != notice_id]
                        save_json(NOTICE_FILE, tour_notices); st.success(_("notice_del_success")); safe_rerun()

                with col_title:
                    st.markdown(f"**{_('content')}:** {notice.get('content', _('no_content'))}")

                    attached_files = notice.get('files', [])
                    if attached_files:
                        st.markdown(f"**{_('attached_files')}:**")
                        for file_info in attached_files: display_and_download_file(file_info, notice_id, is_admin=True, is_user_post=False)
                    else: st.markdown(f"**{_('attached_files')}:** {_('no_files')}")

                # --- 수정 폼 ---
                with st.form(f"update_notice_{notice_id}", clear_on_submit=True):
                    current_type_index = list(type_options_rev.keys()).index(notice_type_key)
                    updated_display_type = st.radio(_("type"), list(type_options_rev.values()), index=current_type_index, key=f"update_type_{notice_id}")
                    updated_type_key = list(type_options_rev.keys())[list(type_options_rev.values()).index(updated_display_type)]

                    updated_content = st.text_area(_("update_content"), value=notice.get('content', ''))

                    if st.form_submit_button(_("update")):
                        for n in tour_notices:
                            if n.get('id') == notice_id:
                                n['content'] = updated_content; n['type'] = updated_type_key; save_json(NOTICE_FILE, tour_notices); st.success(_("notice_upd_success")); safe_rerun()

        # === 6. 수정: 관리자 제목 변경 ===
        st.subheader(f"📸 포스트 관리")
        valid_posts_admin = [p for p in user_posts if isinstance(p, dict) and (p.get('content') or p.get('files'))]
        if not valid_posts_admin: 
            st.write(_("no_posts"))
        else:
            posts_to_display_admin = sorted(valid_posts_admin, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
            for post in posts_to_display_admin:
                post_id = post['id']
                
                with st.expander(f"익명 사용자 - {post.get('date', 'N/A')[:16]} (ID: {post_id[:8]})", expanded=False):
                    st.markdown(f'<div class="notice-content-box">{post.get("content", _("no_content"))}</div>', unsafe_allow_html=True)
                    
                    attached_media = post.get('files', [])
                    if attached_media:
                        st.markdown(f"**{_('attached_files')}:**")
                        # 관리자는 모든 파일을 볼 수 있음 (is_admin=True)
                        for media_file in attached_media:
                            display_and_download_file(media_file, post_id, is_admin=True, is_user_post=True)
                    
                    # 관리자용 삭제 버튼
                    if st.button(_("remove"), key=f"del_post_{post_id}", help="이 포스트를 영구적으로 삭제합니다."):
                        # 파일 먼저 삭제
                        for file_info in post.get('files', []):
                            if os.path.exists(file_info['path']):
                                try:
                                    os.remove(file_info['path'])
                                except Exception as e:
                                    st.warning(f"파일 삭제 실패: {e}")
                        # 목록에서 포스트 제거
                        user_posts[:] = [p for p in user_posts if p.get('id') != post_id]
                        save_json(USER_POST_FILE, user_posts)
                        st.success("포스트가 삭제되었습니다.")
                        safe_rerun()
        # === 수정 끝 ===

    # 2. 일반 사용자 공지사항 & 포스트 보기
    if not st.session_state.admin:
        st.subheader(f"📢 {_('tab_notice')}"); valid_notices = [n for n in tour_notices if isinstance(n, dict) and n.get('title')]
        if not valid_notices: st.write(_("no_notices"))
        else:
            notices_to_display = sorted(valid_notices, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
            type_options_rev = {"General": _("general"), "Urgent": _("urgent")}

            for notice in notices_to_display:
                notice_id = notice.get('id'); notice_type_key = notice.get('type', 'General')
                translated_type = type_options_rev.get(notice_type_key, _("general")); notice_title = notice.get('title', _("no_title"))
                prefix = "🚨 " if notice_type_key == "Urgent" else ""; header_text = f"{prefix}[{translated_type}] {notice_title} - *{notice.get('date', 'N/A')[:16]}*"

                with st.expander(header_text, expanded=False): 
                    st.markdown(f'<div class="notice-content-box">{notice.get("content", _("no_content"))}</div>', unsafe_allow_html=True)
                    attached_files = notice.get('files', [])
                    if attached_files:
                        st.markdown(f"**{_('attached_files')}:**")
                        for file_info in attached_files: display_and_download_file(file_info, notice_id, is_admin=False, is_user_post=False)

        # --- 사용자 포스트 섹션 ---
        st.subheader(f"📸 {_('user_posts')}")

        # --- 사용자 포스트 작성 폼 (일반 사용자 모두 허용) ---
        with st.expander(_("new_post"), expanded=False): 
            with st.form("user_post_form", clear_on_submit=True):
                post_content = st.text_area(_("post_content"), placeholder="여행 후기, 사진 공유 등 자유롭게 작성하세요.")
                uploaded_media = st.file_uploader(_("media_attachment"), type=["png", "jpg", "jpeg", "mp4", "mov"], accept_multiple_files=True, key="user_media_uploader")
                post_submitted = st.form_submit_button(_("register"))

                if post_submitted and (post_content or uploaded_media):
                    media_info_list = save_uploaded_files(uploaded_media)

                    new_post = {"id": str(uuid.uuid4()), "content": post_content, "files": media_info_list, "date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")}
                    user_posts.insert(0, new_post); save_json(USER_POST_FILE, user_posts); st.success(_("post_success")); safe_rerun()
                elif post_submitted: st.warning(_("fill_in_fields"))

        # --- 사용자 포스트 목록 표시 ---
        valid_posts = [p for p in user_posts if isinstance(p, dict) and (p.get('content') or p.get('files'))]
        if not valid_posts: st.write(_("no_posts"))
        else:
            posts_to_display = sorted(valid_posts, key=lambda x: x.get('date', '9999-12-31'), reverse=True)
            for post in posts_to_display:
                post_id = post['id']
                with st.expander(f"익명 사용자 - {post.get('date', 'N/A')[:16]}", expanded=False):
                    st.markdown(f'<div class="notice-content-box">{post.get("content", _("no_content"))}</div>', unsafe_allow_html=True)
                    
                    # === 수정된 부분: 사용자가 모든 첨부파일을 볼 수 있도록 수정 ===
                    attached_media = post.get('files', [])
                    if attached_media:
                        st.markdown(f"**{_('attached_files')}:**")
                        # is_user_post=True를 전달하여 (수정된) display_and_download_file 함수가 파일을 표시하도록 함
                        for media_file in attached_media:
                            display_and_download_file(media_file, post_id, is_admin=False, is_user_post=True)
                    # === 수정 끝 ===

# =============================================================================
# 탭 2: 칸타타 투어 (Map)
# =============================================================================
with tab_map:

    # --- 1. 관리자: 일정 관리 섹션 ---
    if st.session_state.admin:
        st.subheader(f"⚙️ {_('tour_schedule_management')}") # '공연도시 정보 입력'

        # --- 도시/일정 등록 폼 (Admin Only) ---
        with st.expander(_("add_city"), expanded=False): 
            with st.form("schedule_form", clear_on_submit=True):
                col_c, col_d, col_v = st.columns(3)
                registered_cities = {s['city'] for s in tour_schedule if s.get('city')}
                available_cities = [c for c in city_options if c not in registered_cities]

                city_name_input = col_c.selectbox(_('city_name'), options=available_cities, index=0 if available_cities else None, key="new_city_select")
                schedule_date = col_d.date_input(_("date"), key="new_date_input")
                venue_name = col_v.text_input(_("venue"), placeholder=_("venue_placeholder"), key="new_venue_input")

                col_l, col_s, col_ug, col_up = st.columns(4)
                type_options_map = {_("indoor"): "indoor", _("outdoor"): "outdoor"}
                selected_display_type = col_l.radio(_("type"), list(type_options_map.values()))
                type_sel = list(type_options_map.keys())[list(type_options_map.values()).index(selected_display_type)] 

                expected_seats = col_s.number_input(_("seats"), min_value=0, value=500, step=50, help=_("seats_tooltip"))
                
                google_link = col_ug.text_input(f"🚗 {_('google_link')}", placeholder=_("google_link_placeholder"))

                # === 1. 수정: 슬라이더에 % 포맷 적용 ===
                probability = col_up.slider(_("probability"), min_value=0, max_value=100, value=100, step=5, format="%d%%")

                note = st.text_area(_("note"), placeholder=_("note_placeholder"))

                submitted = st.form_submit_button(_("register"))

                if submitted:
                    if not city_name_input or not venue_name or not schedule_date: st.warning(_("fill_in_fields"))
                    elif city_name_input not in city_dict: st.warning(_("city_coords_error"))
                    else:
                        city_coords = city_dict.get(city_name_input, {'lat': 0, 'lon': 0}) 
                        new_schedule_entry = {"id": str(uuid.uuid4()), "city": city_name_input, "venue": venue_name, "lat": city_coords["lat"], "lon": city_coords["lon"], "date": schedule_date.strftime("%Y-%m-%d"), "type": type_sel, "seats": str(expected_seats), "note": note, "google_link": google_link, "probability": probability, "reg_date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")}
                        tour_schedule.append(new_schedule_entry); save_json(CITY_FILE, tour_schedule); st.success(_("schedule_reg_success")); safe_rerun()

        # --- 관리자: 일정 보기 및 수정/삭제 ---
        valid_schedule = [item for item in tour_schedule if isinstance(item, dict) and item.get('id') and item.get('city') and item.get('venue')]

        if valid_schedule:
            st.subheader(_("venue_list_title")) # '공연 도시 목록'
            schedule_dict = {item['id']: item for item in valid_schedule}
            sorted_schedule_items = sorted(schedule_dict.items(), key=lambda x: x[1].get('date', '9999-12-31'))
            type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")}

            for i, (item_id, item) in enumerate(sorted_schedule_items):
                current_type_key = item.get('type', 'outdoor')
                translated_type = type_options_map_rev.get(current_type_key, _("outdoor"))
                probability_val = item.get('probability', 100)

                city_name_display = item.get('city', 'N/A')
                
                # --- 실내/실외 색상 변경 ---
                type_color_md = "#1E90FF" if current_type_key == 'indoor' else "#A52A2A" # 파란색 또는 연한 갈색
                
                # === 2. 수정: expander 제목에서 (:#1E90FF[실내]) 대신 (실내)로 표시 ===
                header_text = f"[{item.get('date', 'N/A')}] **:{'orange'}[{city_name_display}]** - {item['venue']} ({translated_type}) | {_('probability')}: **{probability_val}%**"

                with st.expander(header_text, expanded=False): 

                    with st.form(f"edit_delete_form_{item_id}", clear_on_submit=False):
                        st.markdown(f"**{_('date')}:** {item.get('date', 'N/A')} (등록일: {item.get('reg_date', '')})")

                        col_uc, col_ud, col_uv = st.columns(3)

                        updated_city = col_uc.selectbox(_("city"), city_options, index=city_options.index(item.get('city', "Pune") if item.get('city') in city_options else city_options[0]), key=f"upd_city_{item_id}")

                        try: initial_date = datetime.strptime(item.get('date', '2025-01-01'), "%Y-%m-%d").date()
                        except ValueError: initial_date = date.today()

                        updated_date = col_ud.date_input(_("date"), value=initial_date, key=f"upd_date_{item_id}")
                        updated_venue = col_uv.text_input(_("venue"), value=item.get('venue'), key=f"upd_venue_{item_id}")

                        col_ul, col_us, col_ug, col_up = st.columns(4)
                        current_map_type = item.get('type', 'outdoor')
                        current_map_index = 0 if current_map_type == "indoor" else 1
                        map_type_list = list(type_options_map_rev.values())
                        updated_display_type = col_ul.radio(_("type"), map_type_list, index=current_map_index, key=f"update_map_type_{item_id}")
                        updated_type = "indoor" if updated_display_type == _("indoor") else "outdoor"

                        seats_value = item.get('seats', '0')
                        updated_seats = col_us.number_input(_("seats"), min_value=0, value=int(seats_value) if str(seats_value).isdigit() else 500, step=50, key=f"upd_seats_{item_id}")
                        
                        updated_google = col_ug.text_input(f"🚗 {_('google_link')}", value=item.get('google_link', ''), key=f"upd_google_{item_id}")
                        
                        # === 1. 수정: 슬라이더에 % 포맷 적용 ===
                        updated_probability = col_up.slider(_("probability"), min_value=0, max_value=100, value=item.get('probability', 100), step=5, key=f"upd_prob_{item_id}", format="%d%%")

                        updated_note = st.text_area(_("note"), value=item.get('note'), key=f"upd_note_{item_id}")

                        st.markdown("---")
                        col_save, col_del, col_space = st.columns([1, 1, 4])

                        # "등록" (Save) 버튼
                        with col_save:
                            if st.form_submit_button(_("register"), help="수정 내용을 저장하고 창을 닫습니다"):
                                for idx, s in enumerate(tour_schedule):
                                    if s.get('id') == item_id:
                                        coords = city_dict.get(updated_city, {'lat': s.get('lat', 0), 'lon': s.get('lon', 0)})

                                        tour_schedule[idx].update({
                                            "city": updated_city, "venue": updated_venue, "lat": coords["lat"], "lon": coords["lon"],
                                            "date": updated_date.strftime("%Y-%m-%d"), "type": updated_type, "seats": str(updated_seats),
                                            "note": updated_note, "google_link": updated_google, "probability": updated_probability,
                                        })
                                        save_json(CITY_FILE, tour_schedule)
                                        st.success(_("schedule_upd_success"))
                                        safe_rerun()

                        # "제거" (Remove) 버튼
                        with col_del:
                            if st.form_submit_button(_("remove"), help=_("schedule_del_success")):
                                tour_schedule[:] = [s for s in tour_schedule if s.get('id') != item_id]
                                save_json(CITY_FILE, tour_schedule)
                                st.success(_("schedule_del_success"))
                                safe_rerun()

                    # Display distance/time between current city and the next city in the expander
                    if i < len(sorted_schedule_items) - 1:
                        current_city_coords = (item.get('lat'), item.get('lon'))
                        next_item = sorted_schedule_items[i+1][1]
                        next_city_coords = (next_item.get('lat'), next_item.get('lon'))

                        if all(current_city_coords) and all(next_city_coords):
                            distance_time_info = calculate_distance_and_time(current_city_coords, next_city_coords)
                            st.markdown(f"**<span style='color: #888;'>➡️ {item.get('city')}에서 {next_item.get('city')}까지:</span>** <span style='color: #888;'>{distance_time_info}</span>", unsafe_allow_html=True)
                        else:
                                st.markdown(f"**<span style='color: #888;'>➡️ {item.get('city')}에서 {next_item.get('city')}까지:</span>** <span style='color: #888;'>좌표 정보 불충분</span>", unsafe_allow_html=True)

        else: st.write(_("no_schedule"))


    # --- 지도 표시 (사용자 & 관리자 공통) ---
    st.subheader(f"🗺️ {_('tab_map')} 보기") # '칸타타 투어 보기'
    current_date = date.today()
    schedule_for_map = sorted([s for s in tour_schedule if s.get('date') and s.get('lat') is not None and s.get('lon') is not None and s.get('id')], key=lambda x: x['date'])

    AURANGABAD_COORDS = city_dict.get("Aurangabad", {'lat': 19.876165, 'lon': 75.343314})
    start_coords = [AURANGABAD_COORDS['lat'], AURANGABAD_COORDS['lon']]

    m = folium.Map(location=start_coords, zoom_start=8, tiles="CartoDB positron")
    locations = []
    city_names_for_map = [] 
 
    for item in schedule_for_map:
        lat = item['lat']; lon = item['lon']; date_str_map = item['date']
        city_name_map = item.get('city', 'N/A') 

        try: event_date = datetime.strptime(date_str_map, "%Y-%m-%d").date()
        except ValueError: event_date = current_date + timedelta(days=365)

        is_past = event_date < current_date

        icon_color = '#BB3333'; opacity_val = 0.25 if is_past else 1.0

        type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")}
        translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
        
        # --- 실내/실외 색상 및 아이콘 변경 ---
        type_color_html = "#1E90FF" if item.get('type') == 'indoor' else "#A52A2A" # 파란색 또는 연한 갈색
        map_type_icon_fa = 'fa-building' if item.get('type') == 'indoor' else 'fa-tree' # FontAwesome 아이콘
        
        probability_val = item.get('probability', 100); city_name_display = item.get('city', 'N/A')

        red_city_name = f'<span style="color: #BB3333; font-weight: bold;">{city_name_display}</span>'

        # 팝업 HTML (최소 높이 190px)
        popup_html = f"""
        <div style="color: #1A1A1A; background-color: #FFFFFF; padding: 10px; border-radius: 8px; min-height: 190px;">
            <div style="color: #1A1A1A;">
                <b>{_('city')}:</b> {red_city_name}<br>
                <b>{_('date')}:</b> {date_str_map}<br>
                <b>{_('venue')}:</b> {item.get('venue', 'N/A')}<br>
                <b>{_('type')}:</b> <span style="color: {type_color_html};"><i class="fa {map_type_icon_fa}" style="margin-right: 5px;"></i> {translated_type}</span><br>
                <b>{_('probability')}:</b> <span style="font-weight: bold; color: #66BB66;">{probability_val}%</span>
                
                <div style="width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 10px; margin-top: 5px;">
                    <div style="width: {probability_val}%; background-color: #66BB66; border-radius: 5px; height: 10px;"></div>
                </div>
            </div>
        """

        # === 5. 수정: 구글맵 링크를 내비게이션 URL로 변경 ===
        if item.get('google_link'):
            google_link_data = item['google_link']
            final_google_link = ""

            # 입력값이 URL인지 텍스트인지 확인
            if google_link_data.startswith('http'):
                # URL이면, 기존처럼 링크
                final_google_link = google_link_data
            else:
                # URL이 아니면 (장소 이름이면), 'destination'을 사용한 내비게이션 URL 생성
                encoded_query = quote(f"{google_link_data}, {item.get('city', '')}") # URL 인코딩
                # (수정) 'https://www.google.com/maps/dir/?api=1&destination=' (웹/모바일 호환)
                final_google_link = f"https://www.google.com/maps/dir/?api=1&destination={encoded_query}"

            # 아이콘(갈색, 클릭X)과 텍스트(파란색, 클릭O)를 분리
            popup_html += f"""
                <span style="display: block; margin-top: 5px; font-weight: bold;">
                    <i class="fa fa-car" style="color: #A52A2A; margin-right: 5px;"></i> 
                    <a href="{final_google_link}" target="_blank" 
                       style="color: #1A73E8; text-decoration: none;">
                       {_("google_link")}
                    </a>
                </span>
            """
        # === 수정 끝 ===

        popup_html += "</div>" # 팝업 전체 닫기

        # 마커 아이콘
        city_initial = item.get('city', 'A')[0]
        marker_icon_html = f"""
            <div style="
                transform: scale(0.666);
                opacity: {0.5 if is_past else 1.0};
                text-align: center;
                white-space: nowrap;
            ">
                <i class="fa fa-map-marker fa-3x" style="color: #BB3333;"></i>
                <div style="font-size: 10px; color: black; font-weight: bold; position: absolute; top: 12px; left: 13px;">{city_initial}</div>
            </div>
        """

        folium.Marker([lat, lon], popup=folium.Popup(popup_html, max_width=300), icon=folium.DivIcon(icon_size=(30, 45), icon_anchor=(15, 45), html=marker_icon_html)).add_to(m)
        locations.append([lat, lon])
        city_names_for_map.append(city_name_map) 


    # 4. AntPath (경로 애니메이션) 및 거리/시간 텍스트 배치
    if len(locations) > 1:
        current_index = -1

        for i, item in enumerate(schedule_for_map):
            try:
                event_date = datetime.strptime(item['date'], "%Y-%m-%d").date()
                if event_date >= current_date: current_index = i; break
            except ValueError: continue

        if current_index == -1: past_segments = locations; future_segments = []
        elif current_index == 0: past_segments = []; future_segments = locations
        else: past_segments = locations[:current_index + 1]; future_segments = locations[current_index:]

        # 1. 과거 경로 (투명도 0.125, 구간별 툴팁)
        if len(past_segments) > 1:
            for i in range(len(past_segments) - 1):
                segment = [past_segments[i], past_segments[i+1]]
                dist_time = calculate_distance_and_time(past_segments[i], past_segments[i+1])
                tooltip_text = f"{dist_time}"
                
                tooltip_obj = folium.Tooltip(tooltip_text, sticky=False) 
                
                folium.PolyLine(
                    locations=segment, 
                    color="#BB3333", 
                    weight=5, 
                    opacity=0.125, 
                    tooltip=tooltip_obj 
                ).add_to(m)

        # 2. 미래 경로 (AntPath animation, 구간별 툴팁)
        if len(future_segments) > 1:
            for i in range(len(future_segments) - 1):
                segment = [future_segments[i], future_segments[i+1]]
                dist_time = calculate_distance_and_time(future_segments[i], future_segments[i+1])
                tooltip_text = f"{dist_time}"

                tooltip_obj = folium.Tooltip(tooltip_text, sticky=False)

                AntPath(
                    segment, 
                    use="regular", 
                    dash_array='30, 20', 
                    color='#BB3333', 
                    weight=5, 
                    opacity=0.8, 
                    options={"delay": 24000, "dash_factor": -0.1, "color": "#BB3333"},
                    tooltip=tooltip_obj 
                ).add_to(m)

    # 지도 표시 (전체 너비 활용)
    st_folium(m, width=1000, height=600, key="tour_map_render")

    st.caption(_("caption"))
