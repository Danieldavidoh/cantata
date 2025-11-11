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
        "general": "일반", "urgent": "긴급", "admin_login": "관리자 로그인", "update_content": "내용 수정",
        "existing_notices": "기존 공지사항", "no_notices": "공지사항이 없습니다.", "content": "내용",
        "no_content": "내용 없음", "no_title": "제목 없음", "tour_schedule_management": "투어 일정 관리",
        "set_data": "데이터 설정", "type": "유형", "city": "도시", "link": "링크", "past_route": "지난 경로",
        "single_location": "단일 위치", "legend": "범례", "no_schedule": "일정이 없습니다.",
        "city_coords_error": "좌표를 찾을 수 없습니다. city_dict에 추가해 주세요.",
        "logged_in_success": "관리자로 로그인했습니다.", "logged_out_success": "로그아웃했습니다.",
        "incorrect_password": "비밀번호가 틀렸습니다.", "fill_in_fields": "제목과 내용을 채워주세요.",
        "notice_reg_success": "공지사항이 성공적으로 등록되었습니다!", "notice_del_success": "공지사항이 삭제되었습니다.",
        "notice_upd_success": "공지사항이 수정되었습니다.", "schedule_reg_success": "일정이 등록되었습니다.",
        "schedule_del_success": "일정 항목이 제거되었습니다.", "schedule_upd_success": "일정이 성공적으로 수정되었습니다.",
        "venue_placeholder": "공연 장소를 입력하세요", "note_placeholder": "특이사항을 입력하세요",
        "google_link_placeholder": "구글맵 URL을 입력하세요", "seats_tooltip": "예상 관객 인원",
        "file_attachment": "파일 첨부", "attached_files": "첨부 파일", "no_files": "없음",
        "user_posts": "사용자 포스트",
        "new_post": "새 포스트 작성",
        "post_content": "포스트 내용",
        "media_attachment": "사진/동영상 첨부",
        "post_success": "포스트가 성공적으로 업로드되었습니다!",
        "no_posts": "현재 포스트가 없습니다.",
        "admin_only_files": "첨부 파일은 관리자만 확인 가능합니다.",
        "probability": "가능성",
        "caption": "지도 위의 아이콘이나 경로를 클릭하여 세부 정보를 확인하세요." # 캡션 추가
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date", "city_name": "City Name", "search_placeholder": "Search City/Venue...",

        # Additional translations
        "general": "General", "urgent": "Urgent", "admin_login": "Admin Login", "update_content": "Update Content",
        "existing_notices": "Existing Notices", "no_notices": "No notices available.", "content": "Content",
        "no_content": "No Content", "no_title": "No Title", "tour_schedule_management": "Tour Schedule Management",
        "set_data": "Set Data", "type": "Type", "city": "City", "link": "Link", "past_route": "Past Route",
        "single_location": "Single Location", "legend": "Legend", "no_schedule": "No schedule available.",
        "city_coords_error": "Coordinates not found. Please add to city_dict.", "logged_in_success": "Logged in as Admin.",
        "logged_out_success": "Logged out.", "incorrect_password": "Incorrect password.",
        "fill_in_fields": "Please fill in the title and content.", "notice_reg_success": "Notice registered successfully!",
        "notice_del_success": "Notice deleted.", "notice_upd_success": "Notice updated.",
        "schedule_reg_success": "Schedule registered.", "schedule_del_success": "Schedule entry removed.",
        "schedule_upd_success": "Schedule updated successfully.", "venue_placeholder": "Enter venue name",
        "note_placeholder": "Enter notes/special remarks", "google_link_placeholder": "Enter Google Maps URL",
        "seats_tooltip": "Expected audience count", "file_attachment": "File Attachment", "attached_files": "Attached Files",
        "no_files": "None", "user_posts": "User Posts", "new_post": "Create New Post", "post_content": "Post Content",
        "media_attachment": "Attach Photo/Video", "post_success": "Post uploaded successfully!", "no_posts": "No posts available.",
        "admin_only_files": "Attached files can only be viewed by Admin.", "probability": "Probability",
        "caption": "Click icons or routes on the map for details." # 캡션 추가
    },
    "hi": {
        "title_cantata": "कंटटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "टूर रूट", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख", "city_name": "शहर का नाम", "search_placeholder": "शहर/स्थल खोजें...",

        # Additional translations
        "general": "सामान्य", "urgent": "तत्काल", "admin_login": "व्यवस्थापक लॉगिन", "update_content": "सामग्री अपडेट करें",
        "existing_notices": "मौजूदा सूचनाएं", "no_notices": "कोई सूचना उपलब्ध नहीं है।", "content": "सामग्री",
        "no_content": "कोई सामग्री नहीं", "no_title": "कोई शीर्षक नहीं", "tour_schedule_management": "टूर अनुसूची प्रबंधन",
        "set_data": "डेटा सेट करें", "type": "प्रकार", "city": "शहर", "link": "लिंक", "past_route": "पिछला मार्ग",
        "single_location": "एकल स्थान", "legend": "किंवंती", "no_schedule": "कोई कार्यक्रम उपलब्ध नहीं है।",
        "city_coords_error": "निर्देशांक नहीं मिला। कृपया city_dict में जोड़ें।", "logged_in_success": "व्यवस्थापक के रूप में लॉग इन किया गया।",
        "logged_out_success": "लॉग आउट किया गया।", "incorrect_password": "गलत पासवर्ड।",
        "fill_in_fields": "कृपया शीर्षक और सामग्री भरें।", "notice_reg_success": "सूचना सफलतापूर्वक पंजीकृत हुई!",
        "notice_del_success": "सूचना हटा दी गई।", "notice_upd_success": "सूचना अपडेट की गई।",
        "schedule_reg_success": "कार्यक्रम पंजीकृत हुआ।", "schedule_del_success": "कार्यक्रम प्रविष्टि हटा दी गई।",
        "schedule_upd_success": "कार्यक्रम सफलतापूर्वक अपडेट किया गया।", "venue_placeholder": "स्थल का नाम दर्ज करें",
        "note_placeholder": "नोट्स/विशेष टिप्पणी दर्ज करें", "google_link_placeholder": "गूगल मैप्स URL दर्ज करें",
        "seats_tooltip": "अपेक्षित दर्शक संख्या",
        "file_attachment": "फ़ाइल संलग्नक", "attached_files": "संलग्न फ़ाइलें", "no_files": "कोई नहीं",
        "user_posts": "उपयोगकर्ता पोस्ट", "new_post": "नई पोस्ट बनाएं", "post_content": "Post सामग्री",
        "media_attachment": "फोटो/वीडियो संलग्न करें", "post_success": "पोस्ट सफलतापूर्वक अपलोड हुई!", "no_posts": "कोई पोस्ट उपलब्ध नहीं है।",
        "admin_only_files": "Attached files can only be viewed by Admin.", "probability": "संभावना",
        "caption": "विवरण के लिए मानचित्र पर आइकन या मार्गों पर क्लिक करें।" # 캡션 추가
    }
}

# --- 세션 초기화 ---
defaults = {"admin": False, "lang": "ko", "notice_open": False, "map_open": False, "logged_in_user": None, "show_login_form": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v
    elif k == "lang" and not isinstance(st.session_state.lang, str): st.session_state[k] = "ko"

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
                    st.download_button(label=f"⬇️ {icon} {file_name} ({file_size_kb} KB)", data=f.read(), file_name=file_name, mime=file_type, key=f"downloader_{key_prefix}_{notice_id}_{file_name}")
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
# 6. 제목
# ----------------------------------------------------------------------
title_cantata = _('title_cantata')
title_year = _('title_year')
title_region = _('title_region')

# 요청된 스타일 적용 (빨강, 흰색, 녹색/축소)
title_html = f"""
    <span style="color: #BB3333; margin-right: 10px;">{title_cantata}</span>
    <span style="color: #FFFFFF; margin-right: 10px;">{title_year}</span>
    <span style="color: #66BB66; font-size: 66%;">{title_region}</span>
"""
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)


# 언어 선택 버튼 (상단 고정)
col_lang, col_auth = st.columns([1, 3])
with col_lang:
    LANG_OPTIONS = {"ko": "한국어", "en": "English", "hi": "हिन्दी"}
    lang_keys = list(LANG_OPTIONS.keys())
    lang_display_names = list(LANG_OPTIONS.values())

    current_lang_index = lang_keys.index(st.session_state.lang)

    selected_lang_display = st.selectbox(
        _("menu"),
        options=lang_display_names,
        index=current_lang_index,
        key="lang_select"
    )

    selected_lang_key = lang_keys[lang_display_names.index(selected_lang_display)]

    if selected_lang_key != st.session_state.lang:
        st.session_state.lang = selected_lang_key
        st.rerun()

# --- 로그인 / 로그아웃 로직 ---
def safe_rerun():
    if hasattr(st, 'rerun'): st.rerun()

def handle_login_button_click():
    st.session_state.show_login_form = not st.session_state.show_login_form
    safe_rerun()

with col_auth:
    if st.session_state.admin:
        if st.button(_("logout"), key="logout_btn"):
            st.session_state.admin = False
            st.session_state.logged_in_user = None
            st.session_state.show_login_form = False
            safe_rerun()
    else:
        if st.button(_("login"), key="login_btn"): handle_login_button_click()

        if st.session_state.show_login_form:
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

# --- 탭 구성 ---
tab_notice, tab_map = st.tabs([_("tab_notice"), _("tab_map")])

# =============================================================================
# 탭 1: 공지사항 (Notice)
# =============================================================================
with tab_notice:

    # 1. 관리자 공지사항 관리
    if st.session_state.admin:
        st.subheader(f"🔔 {_('existing_notices')} (관리자 모드)")

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
                post_id = post['id']; st.markdown(f"**익명 사용자** - *{post.get('date', 'N/A')[:16]}*")
                st.markdown(f'<div class="notice-content-box">{post.get("content", _("no_content"))}</div>', unsafe_allow_html=True)
                attached_media = post.get('files', [])
                if attached_media: display_and_download_file(attached_media[0], post_id, is_admin=False, is_user_post=True)
                st.markdown("---")

# =============================================================================
# 탭 2: 투어 경로 (Map) - 지도만 표시 (관리자 모드 박스 제거 완료)
# =============================================================================
with tab_map:

    # --- 1. 관리자: 일정 관리 섹션 ---
    if st.session_state.admin:
        st.subheader(f"⚙️ {_('tour_schedule_management')}")

        # --- 도시/일정 등록 폼 (Admin Only) ---
        with st.expander(_("add_city"), expanded=False):
            with st.form("schedule_form", clear_on_submit=True):
                col_c, col_d, col_v = st.columns(3)
                # 도시 이름 중복 방지 로직 (등록된 도시 제외)
                registered_cities = {s['city'] for s in tour_schedule if s.get('city')}
                available_cities = [c for c in city_options if c not in registered_cities]

                # Ensure 'city_name' is correctly translated in the selectbox label
                city_name_input = col_c.selectbox(_('city_name'), options=available_cities, index=0 if available_cities else None, key="new_city_select")
                schedule_date = col_d.date_input(_("date"), key="new_date_input")
                venue_name = col_v.text_input(_("venue"), placeholder=_("venue_placeholder"), key="new_venue_input")

                col_l, col_s, col_ug, col_up = st.columns(4)
                type_options_map = {_("indoor"): "indoor", _("outdoor"): "outdoor"}
                selected_display_type = col_l.radio(_("type"), list(type_options_map.keys()))
                type_sel = type_options_map[selected_display_type]

                expected_seats = col_s.number_input(_("seats"), min_value=0, value=500, step=50, help=_("seats_tooltip"))
                google_link = col_ug.text_input(_("google_link"), placeholder=_("google_link_placeholder"))
                probability = col_up.slider(_("probability"), min_value=0, max_value=100, value=100, step=5)

                note = st.text_area(_("note"), placeholder=_("note_placeholder"))

                submitted = st.form_submit_button(_("register"))

                if submitted:
                    if not city_name_input or not venue_name or not schedule_date: st.warning(_("fill_in_fields"))
                    elif city_name_input not in city_dict: st.warning(_("city_coords_error"))
                    else:
                        city_coords = city_dict.get(city_name_input, {'lat': 0, 'lon': 0}) # Added .get() with default value
                        new_schedule_entry = {"id": str(uuid.uuid4()), "city": city_name_input, "venue": venue_name, "lat": city_coords["lat"], "lon": city_coords["lon"], "date": schedule_date.strftime("%Y-%m-%d"), "type": type_sel, "seats": str(expected_seats), "note": note, "google_link": google_link, "probability": probability, "reg_date": datetime.now(timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M:%S")}
                        tour_schedule.append(new_schedule_entry); save_json(CITY_FILE, tour_schedule); st.success(_("schedule_reg_success")); safe_rerun()

        # --- 관리자: 일정 보기 및 수정/삭제 ---
        valid_schedule = [item for item in tour_schedule if isinstance(item, dict) and item.get('id') and item.get('city') and item.get('venue')]

        if valid_schedule:
            st.subheader(_("tour_schedule_management"))
            schedule_dict = {item['id']: item for item in valid_schedule}
            sorted_schedule_items = sorted(schedule_dict.items(), key=lambda x: x[1].get('date', '9999-12-31'))
            type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")}

            # Display current schedule entries with distance/time between them
            for i, (item_id, item) in enumerate(sorted_schedule_items):
                translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
                probability_val = item.get('probability', 100)

                # Apply formatting for the expander header using Markdown
                city_name_display = item.get('city', 'N/A')
                
                # Set markdown color for type
                type_color_md = "blue" if item.get('type') == 'indoor' else "orange" # 가독성을 위해 yellow 대신 orange 사용
                
                # Construct the header text for the expander with Markdown formatting
                header_text = f"[{item.get('date', 'N/A')}] **:{'orange'}[{city_name_display}]** - {item['venue']} (:{type_color_md}[{translated_type}]) | {_('probability')}: **{probability_val}%**"

                with st.expander(header_text, expanded=False):

                    # --- 수정 폼 (수정된 수정/등록 및 제거 버튼 포함) ---
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
                        updated_google = col_ug.text_input(_("google_link"), value=item.get('google_link', ''), key=f"upd_google_{item_id}")
                        updated_probability = col_up.slider(_("probability"), min_value=0, max_value=100, value=item.get('probability', 100), step=5, key=f"upd_prob_{item_id}")

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
                            st.markdown(f"**<span style='color: grey;'>➡️ {item.get('city')}에서 {next_item.get('city')}까지:</span>** <span style='color: grey;'>{distance_time_info}</span>", unsafe_allow_html=True)
                        else:
                                st.markdown(f"**<span style='color: grey;'>➡️ {item.get('city')}에서 {next_item.get('city')}까지:</span>** <span style='color: grey;'>좌표 정보 불충분</span>", unsafe_allow_html=True)

        else: st.write(_("no_schedule"))


    # --- 지도 표시 (사용자 & 관리자 공통) ---
    st.subheader(f"🗺️ {_('tab_map')} 보기")
    current_date = date.today()
    schedule_for_map = sorted([s for s in tour_schedule if s.get('date') and s.get('lat') is not None and s.get('lon') is not None and s.get('id')], key=lambda x: x['date'])

    AURANGABAD_COORDS = city_dict.get("Aurangabad", {'lat': 19.876165, 'lon': 75.343314})
    start_coords = [AURANGABAD_COORDS['lat'], AURANGABAD_COORDS['lon']]

    m = folium.Map(location=start_coords, zoom_start=8, tiles="CartoDB positron")
    locations = []
    city_names_for_map = [] # 도시 이름 저장은 팝업을 위해 유지
 
    for item in schedule_for_map:
        lat = item['lat']; lon = item['lon']; date_str_map = item['date']
        city_name_map = item.get('city', 'N/A') # 도시 이름은 여기서 계속 저장

        try: event_date = datetime.strptime(date_str_map, "%Y-%m-%d").date()
        except ValueError: event_date = current_date + timedelta(days=365)

        is_past = event_date < current_date

        # 아이콘 설정
        icon_color = '#BB3333'; opacity_val = 0.25 if is_past else 1.0

        # 팝업 내용
        type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")}
        translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor")); map_type_icon = '🏠' if item.get('type') == 'indoor' else '🌳'
        probability_val = item.get('probability', 100); city_name_display = item.get('city', 'N/A')

        # 팝업 UI 수정: 흰색 배경, 빨간색 도시명
        red_city_name = f'<span style="color: #BB3333; font-weight: bold;">{city_name_display}</span>'

        # Apply color to type text in popup
        type_color = "blue" if item.get('type') == 'indoor' else "yellow"


        # 팝업 HTML 전체를 흰색 배경으로 설정
        popup_html = f"""
        <div style="color: #1A1A1A; background-color: #FFFFFF; padding: 10px; border-radius: 8px;">
            <div style="color: #1A1A1A;">
                <b>{_('city')}:</b> {red_city_name}<br>
                <b>{_('date')}:</b> {date_str_map}<br>
                <b>{_('venue')}:</b> {item.get('venue', 'N/A')}<br>
                <b>{_('type')}:</b> <span style="color: {type_color};">{map_type_icon} {translated_type}</span><br>
                <b>{_('probability')}:</b> <span style="font-weight: bold; color: #66BB66;">{probability_val}%</span>
                
                <div style="width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 10px; margin-top: 5px;">
                    <div style="width: {probability_val}%; background-color: #66BB66; border-radius: 5px; height: 10px;"></div>
                </div>

            </div>
        """

        # === 수정된 부분: 구글맵 링크에 'fa-car' 아이콘 추가 ===
        if item.get('google_link'):
            google_link_url = item['google_link']
            # 아이콘(<i ...>)과 텍스트(_("google_link")) 모두 <a> 태그 안에 위치시킴
            popup_html += f"""
                <a href="{google_link_url}" target="_blank" 
                   style="color: #1A73E8; text-decoration: none; display: block; margin-top: 5px; font-weight: bold;">
                   <i class="fa fa-car"></i> {_("google_link")}
                </a>
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
        city_names_for_map.append(city_name_map) # 팝업을 위해 도시 이름 리스트는 유지


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

        # 1. 과거 경로 (25% 투명도, 구간별 툴팁)
        if len(past_segments) > 1:
            for i in range(len(past_segments) - 1):
                segment = [past_segments[i], past_segments[i+1]]
                dist_time = calculate_distance_and_time(past_segments[i], past_segments[i+1])
                tooltip_text = f"{dist_time}"
                
                # 툴팁을 라인 중앙에 고정 (sticky=False)
                tooltip_obj = folium.Tooltip(tooltip_text, sticky=False) 
                
                folium.PolyLine(
                    locations=segment, 
                    color="#BB3333", 
                    weight=5, 
                    opacity=0.25, 
                    tooltip=tooltip_obj # Tooltip 객체 전달
                ).add_to(m)

        # 2. 미래 경로 (AntPath animation, 구간별 툴팁)
        if len(future_segments) > 1:
            for i in range(len(future_segments) - 1):
                segment = [future_segments[i], future_segments[i+1]]
                dist_time = calculate_distance_and_time(future_segments[i], future_segments[i+1])
                tooltip_text = f"{dist_time}"

                # 툴팁을 라인 중앙에 고정 (sticky=False)
                tooltip_obj = folium.Tooltip(tooltip_text, sticky=False)

                AntPath(
                    segment, 
                    use="regular", 
                    dash_array='30, 20', 
                    color='#BB3333', 
                    weight=5, 
                    opacity=0.8, 
                    options={"delay": 24000, "dash_factor": -0.1, "color": "#BB3333"},
                    tooltip=tooltip_obj # Tooltip 객체 전달
                ).add_to(m)

    # 지도 표시 (전체 너비 활용)
    st_folium(m, width=1000, height=600, key="tour_map_render")

    st.caption(_("caption"))
