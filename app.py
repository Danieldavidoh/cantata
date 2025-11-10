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
        "probability": "가능성"  # <-- 수정됨: (%) 제거
    },
    "en": {
        "title_cantata": "Cantata Tour", "title_year": "2025", "title_region": "Maharashtra",
        "tab_notice": "Notice", "tab_map": "Tour Route", "indoor": "Indoor", "outdoor": "Outdoor",
        "venue": "Venue", "seats": "Expected", "note": "Note", "google_link": "Google Maps",
        "warning": "Enter city and venue", "delete": "Remove", "menu": "Menu", "login": "Login", "logout": "Logout",
        "add_city": "Add", "register": "Register", "update": "Update", "remove": "Remove",
        "date": "Date", "city_name": "City Name", "search_placeholder": "Search City/Venue...",
        
        # Additional translations
        "general": "General", "urgent": "Urgent",
        "admin_login": "Admin Login",
        "update_content": "Update Content",
        "existing_notices": "Existing Notices",
        "no_notices": "No notices available.",
        "content": "Content",
        "no_content": "No Content",
        "no_title": "No Title",
        "tour_schedule_management": "Tour Schedule Management",
        "set_data": "Set Data",
        "type": "Type",
        "city": "City",
        "link": "Link",
        "past_route": "Past Route",
        "single_location": "Single Location",
        "legend": "Legend",
        "no_schedule": "No schedule available.",
        "city_coords_error": "Coordinates not found. Please add to city_dict.",
        "logged_in_success": "Logged in as Admin.",
        "logged_out_success": "Logged out.",
        "incorrect_password": "Incorrect password.",
        "fill_in_fields": "Please fill in the title and content.",
        "notice_reg_success": "Notice registered successfully!",
        "notice_del_success": "Notice deleted.",
        "notice_upd_success": "Notice updated.",
        "schedule_reg_success": "Schedule registered.",
        "schedule_del_success": "Schedule entry removed.",
        "schedule_upd_success": "Schedule updated successfully.",
        "venue_placeholder": "Enter venue name",
        "note_placeholder": "Enter notes/special remarks",
        "google_link_placeholder": "Enter Google Maps URL",
        "seats_tooltip": "Expected audience count",
        "file_attachment": "File Attachment",
        "attached_files": "Attached Files",
        "no_files": "None",
        "user_posts": "User Posts",
        "new_post": "Create New Post",
        "post_content": "Post Content",
        "media_attachment": "Attach Photo/Video",
        "post_success": "Post uploaded successfully!",
        "no_posts": "No posts available.",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "Probability" # <-- 수정됨: (%) 제거
    },
    "hi": {
        "title_cantata": "कंटटा टूर", "title_year": "२०२५", "title_region": "महाराष्ट्र",
        "tab_notice": "सूचना", "tab_map": "टूर रूट", "indoor": "इनडोर", "outdoor": "आउटडोर",
        "venue": "स्थल", "seats": "अपेक्षित", "note": "नोट", "google_link": "गूगल मैप्स",
        "warning": "शहर और स्थल दर्ज करें", "delete": "हटाएं", "menu": "मेनू", "login": "लॉगिन", "logout": "लॉगआउट",
        "add_city": "जोड़ें", "register": "रजिस्टर", "update": "अपडेट", "remove": "हटाएं",
        "date": "तारीख", "city_name": "शहर का नाम", "search_placeholder": "शहर/स्थल खोजें...",
        
        # Additional translations
        "general": "सामान्य", "urgent": "तत्काल",
        "admin_login": "व्यवस्थापक लॉगिन",
        "update_content": "सामग्री अपडेट करें",
        "existing_notices": "मौजूदा सूचनाएं",
        "no_notices": "कोई सूचना उपलब्ध नहीं है।",
        "content": "सामग्री",
        "no_content": "कोई सामग्री नहीं",
        "no_title": "कोई शीर्षक नहीं",
        "tour_schedule_management": "टूर अनुसूची प्रबंधन",
        "set_data": "डेटा सेट करें",
        "type": "प्रकार",
        "city": "शहर",
        "link": "लिंक",
        "past_route": "पिछला मार्ग",
        "single_location": "एकल स्थान",
        "legend": "किंवदंती",
        "no_schedule": "कोई कार्यक्रम उपलब्ध नहीं है。",
        "city_coords_error": "निर्देशांक नहीं मिला। कृपया city_dict में जोड़ें।",
        "logged_in_success": "व्यवस्थापक के रूप में लॉग इन किया गया।",
        "logged_out_success": "लॉग आउट किया गया।",
        "incorrect_password": "गलत पासवर्ड।",
        "fill_in_fields": "कृपया शीर्षक और सामग्री भरें।",
        "notice_reg_success": "सूचना सफलतापूर्वक पंजीकृत हुई!",
        "notice_del_success": "सूचना हटा दी गई।",
        "notice_upd_success": "सूचना अपडेट की गई।",
        "schedule_reg_success": "कार्यक्रम पंजीकृत हुआ।",
        "schedule_del_success": "कार्यक्रम प्रविष्टि हटा दी गई।",
        "schedule_upd_success": "कार्यक्रम सफलतापूर्वक अपडेट किया गया।",
        "venue_placeholder": "स्थल का नाम दर्ज करें",
        "note_placeholder": "नोट्स/विशेष टिप्पणी दर्ज करें",
        "google_link_placeholder": "गूगल मैप्स URL दर्ज करें",
        "seats_tooltip": "अपेक्षित दर्शक संख्या",
        "file_attachment": "फ़ाइल संलग्नक",
        "attached_files": "संलग्न फ़ाइलें",
        "no_files": "कोई नहीं",
        "user_posts": "उपयोगकर्ता पोस्ट",
        "new_post": "नई पोस्ट बनाएं",
        "post_content": "पो스트 सामग्री",
        "media_attachment": "फोटो/वीडियो संलग्न करें",
        "post_success": "पो스트 सफलतापूर्वक अपलोड हुई!",
        "no_posts": "कोई पोस्ट उपलब्ध नहीं है。",
        "admin_only_files": "Attached files can only be viewed by Admin.",
        "probability": "संभावना"
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
            with open(file_path, "wb") as f: 
                f.write(uploaded_file.getbuffer())
            file_info_list.append({"name": uploaded_file.name, "path": file_path, "type": uploaded_file.type, "size": uploaded_file.size})
        except Exception: 
            pass
    return file_info_list

# --- 파일 Base64 인코딩 함수 (추가) ---
def get_file_as_base64(file_path):
    """파일 경로를 받아 Base64 문자열을 반환합니다."""
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
    """두 좌표 사이의 거리와 예상 소요 시간을 문자열로 반환합니다."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    distance_km = haversine(lat1, lon1, lat2, lon2)
    
    # 거리에 따라 예상 평균 속도 적용
    avg_speed_kmh = 60 if distance_km < 500 else 80
        
    travel_time_h = distance_km / avg_speed_kmh
    
    # 거리 형식 지정
    distance_str = f"{distance_km:.1f} km"
    
    # 시간 형식 지정 (HH시간 MM분)
    hours = int(travel_time_h)
    minutes = int((travel_time_h - hours) * 60)
    
    # 한국어로 거리 및 시간 정보 문자열 구성
    time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"

    return f"거리: {distance_str} | 예상 시간: {time_str}"

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
# ----------------------------------------------------------------------
# 6. 제목
# ----------------------------------------------------------------------
title_text = _["title"]
if lang == "ko":
    parts = title_text.split()
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{" ".join(parts[1:])}</span>'
else:
    parts = title_text.rsplit(" ", 1)
    title_html = f'<span class="main">{parts[0]}</span> <span class="year">{parts[1] if len(parts)>1 else ""}</span>'
st.markdown(f'<h1 class="christmas-title">{title_html}</h1>', unsafe_allow_html=True)
# ----------------------------------------------------------------------
# 7. 헬퍼
# ----------------------------------------------------------------------
def target(): return st.session_state.admin_venues if st.session_state.admin else st.session_state.venues
def date_str(c): d = st.session_state.dates.get(c); return d.strftime(_["date_format"]) if d else "TBD"
# 구글 지도 길찾기 링크 생성 함수
def nav(url): 
    """Google Maps 길찾기 링크 생성 (출발지=현재위치)"""
    # URL 인코딩은 Marker/PolyLine 생성 시 개별적으로 적용해야 안전합니다.
    return f"https://www.google.com/maps/dir/?api=1&destination={url}&travelmode=driving" if url and url.startswith("http") else ""

# ----------------------------------------------------------------------
# 8. 왼쪽 컬럼
# ----------------------------------------------------------------------
left, right = st.columns([1,3])
with left:
    # ------------------------------------------------------------------
    # 도시 추가 UI (도시 추가 시 중복 방지)
    # ------------------------------------------------------------------
    avail = [c for c in avail if c not in st.session_state.route]
    if avail:
        c1, c2 = st.columns([2,1])
        with c1:
            # 선택된 도시는 route에 추가되지 않은 도시 목록에서만 선택 가능 (중복 방지)
            next_city = st.selectbox(_["select_city"], avail, key="next_city_select_v2")
        with c2:
            st.markdown("<br>", unsafe_allow_html=True) 
            if st.button(_["add_city_btn"], key="add_city_btn_v2"):
                st.session_state.route.append(next_city)
                st.rerun()
    st.markdown("---")
    
    # ------------------------------------------------------------------
    # 등록된 도시 목록 (도시 추가 기능 구현을 위해 임시로 재구성)
    # ------------------------------------------------------------------
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
            
            # 아이콘 (자동차 모양) 설정
            icon_in_title = f' <a href="{nav_link}" target="_blank" style="text-decoration:none;font-size:1.2em;">🚗</a>' if nav_link else ''
            
            title_html_content = f"**{city}** – {date_str(city)} ({venue_count} {_['venue']}){icon_in_title}"

            with st.expander(title_html_content, expanded=False, key=f"expander_{city}"):
                
                # 1. 공연 날짜 입력 (달력만 사용)
                cur = st.session_state.dates.get(city, datetime.now().date())
                new = st.date_input(_["performance_date"], cur, key=f"date_{city}_v2")
                if new != cur: st.session_state.dates[city] = new; st.success(_["date_changed"]); st.rerun()
                
                # 2. 등록 폼 (관리자/손님 모드일 때만)
                if st.session_state.admin or st.session_state.guest_mode:
                    
                    # 폼을 컨테이너로 감싸서 UI 정리
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
                        
                        # 등록 버튼 (창을 닫는 기능 포함)
                        submitted = st.form_submit_button(_["register"])
                        
                        if submitted:
                            if not venue_name: st.error(_["enter_venue_name"])
                            else:
                                new_row = pd.DataFrame([{"Venue": venue_name, "Seats": seats, "IndoorOutdoor": selected_type, "Google Maps Link": google_link, "Special Notes": note, "Probability": probability}])
                                t[city] = pd.concat([t.get(city, pd.DataFrame(columns=cols)), new_row], ignore_index=True)
                                st.success(_["venue_registered"])
                                # 등록 후 입력 필드 초기화 및 expander 닫기
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
                                # 삭제 로직
                                t[city] = t[city].drop(idx).reset_index(drop=True)
                                if t[city].empty: t.pop(city, None)
                                st.success(_["schedule_del_success"])
                                st.rerun()
                                
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # 수정 폼
                        if st.session_state.get(edit_key, False):
                            with st.form(f"edit_form_{city}_{idx}_v2"):
                                # ... (수정 폼 내용)
                                st.form_submit_button(_["save"])
                                # ... (수정 폼 저장 로직)
                                
                    
# ----------------------------------------------------------------------
# 9. 오른쪽 컬럼 – 지도 (전체화면, 경로선에 거리/시간 표시)
# ----------------------------------------------------------------------
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
        lat = item['lat']
        lon = item['lon']
        date_str_map = item['date']
        
        try: event_date = datetime.strptime(date_str_map, "%Y-%m-%d").date()
        except ValueError: event_date = current_date + timedelta(days=365)
        
        is_past = event_date < current_date
        
        # 팝업 내용
        type_options_map_rev = {"indoor": _("indoor"), "outdoor": _("outdoor")}
        translated_type = type_options_map_rev.get(item.get('type', 'outdoor'), _("outdoor"))
        map_type_icon = '🏠' if item.get('type') == 'indoor' else '🌳'
        probability_val = item.get('probability', 100)
        city_name_display = item.get('city', 'N/A')
        
        red_city_name = f'<span style="color: #BB3333; font-weight: bold;">{city_name_display}</span>'
        prob_bar_color = "red" if probability_val < 50 else "gold" if probability_val < 90 else "#66BB66"
        prob_bar_html = f"""
        <div style="margin-top: 5px; color: #1A1A1A;">
            <b>{_('probability')}:</b>
            <div style="width: 100%; height: 10px; background-color: #DDD; border-radius: 5px; overflow: hidden; margin-top: 3px;">
                <div style="width: {probability_val}%; height: 100%; background-color: {prob_bar_color};"></div>
            </div>
            <span style="font-size: 12px; font-weight: bold; color: {prob_bar_color};">{probability_val}</span>
        </div>
        """
        
        popup_html = f"""
        <div style="color: #1A1A1A; background-color: #FFFFFF; padding: 10px; border-radius: 8px;">
            <div style="color: #1A1A1A;">
                <b>{_('city')}:</b> {red_city_name}<br>
                <b>{_('date')}:</b> {date_str_map}<br>
                <b>{_('venue')}:</b> {item.get('venue', 'N/A')}<br>
                <b>{_('type')}:</b> {map_type_icon} {translated_type}<br>
                {prob_bar_html}
            </div>
        """
        
        if item.get('google_link'):
            google_link_url = item['google_link']
            popup_html += f'<a href="{google_link_url}" target="_blank" style="color: #1A73E8; text-decoration: none; display: block; margin-top: 5px; font-weight: bold;">{_("google_link")}</a>'
        
        popup_html += "</div>"
        
        city_initial = item.get('city', 'A')[0]
        marker_icon_html = f"""
            <div style="
                transform: scale(0.666); 
                opacity: {0.5 if is_past else 1.0}; /* 과거 도시 투명도 적용 */
                text-align: center;
                white-space: nowrap;
            ">
                <i class="fa fa-map-marker fa-3x" style="color: #BB3333;"></i>
                <div style="font-size: 10px; color: black; font-weight: bold; position: absolute; top: 12px; left: 13px;">{city_initial}</div>
            </div>
        """
        
        folium.Marker([lat, lon], popup=folium.Popup(popup_html, max_width=300), icon=folium.DivIcon(icon_size=(30, 45), icon_anchor=(15, 45), html=marker_icon_html)).add_to(m)
        locations.append([lat, lon])

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

        # 1. 과거 경로 (25% 투명도)
        if len(past_segments) > 1:
            folium.PolyLine(locations=past_segments, color="#BB3333", weight=5, opacity=0.25, tooltip=_("past_route")).add_to(m)
            
        # 2. 미래 경로 (AntPath 애니메이션 및 거리/시간 라벨)
        if len(future_segments) > 1:
            AntPath(future_segments, use="regular", dash_array='30, 20', color='#BB3333', weight=5, opacity=0.8, options={"delay": 24000, "dash_factor": -0.1, "color": "#BB3333"}).add_to(m)

            # --- 연결선 위에 거리/시간 텍스트 배치 ---
            for i in range(len(future_segments) - 1):
                p1 = future_segments[i]
                p2 = future_segments[i+1]
                segment_info = calculate_distance_and_time(p1, p2)
                mid_lat, mid_lon = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                bearing = degrees(atan2(p2[1] - p1[1], p2[0] - p1[0]))
                
                # 텍스트 마커 (DivIcon) 생성
                folium.Marker(
                    [mid_lat, mid_lon], 
                    icon=folium.DivIcon(
                        icon_size=(150, 20),
                        icon_anchor=(75, 10),
                        html=f'''
                            <div style="
                                transform: translate(-50%,-50%) rotate({bearing}deg); 
                                background-color: rgba(45, 45, 45, 0.7); 
                                color: #FAFAFA; 
                                padding: 3px 8px;
                                border-radius: 5px;
                                font-weight: bold;
                                font-size: 11px;
                                border: 1px solid #BB3333;
                                white-space: nowrap;
                            ">
                            {segment_info}
                            </div>
                        '''
                    )
                ).add_to(m)

# 지도 표시 (전체 너비 활용)
st_folium(m, width=700, height=500, key="tour_map_render") # key 추가
    
st.caption(_["caption"])
