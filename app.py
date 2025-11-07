# app.py - 칸타타 투어 2025 (Leaflet 기반 전체 패치)
import streamlit as st
from datetime import datetime, date
import json, os, uuid, base64, re
from math import radians, sin, cos, sqrt, asin
import requests
from pytz import timezone

# --- 설정 ---
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")
NOTICE_FILE = "notice.json"
UPLOAD_DIR = "uploads"
CITY_FILE = "cities.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 기본 세션 상태 ---
defaults = {
    "admin": False, "lang": "ko", "edit_city": None, "expanded": {}, "adding_cities": [],
    "pw": "0009", "seen_notices": [], "active_tab": "공지", "new_notice": False, "sound_played": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- 다국어(간단) ---
LANG = {
    "ko": {"title_base": "칸타타 투어", "caption": "마하라스트라", "tab_notice": "공지", "tab_map": "투어 경로",
           "map_title": "경로 보기", "add_city": "도시 추가", "password": "비밀번호", "login": "로그인",
           "logout": "로그아웃", "wrong_pw": "비밀번호가 틀렸습니다.", "select_city": "도시 선택",
           "venue": "공연장소", "seats": "예상 인원", "note": "특이사항", "google_link": "구글맵 링크",
           "indoor": "실내", "outdoor": "실외", "register": "등록", "edit": "수정", "remove": "삭제",
           "date": "등록일", "performance_date": "공연 날짜", "cancel": "취소", "title_label": "제목",
           "content_label": "내용", "upload_image": "이미지 업로드", "upload_file": "파일 업로드",
           "submit": "등록", "warning": "제목과 내용을 모두 입력해주세요.", "file_download": "파일 다운로드",
           "pending": "미정", "est_time": "{hours}h {mins}m", "new_notice_alert": "따끈한 공지가 도착했어요!"
           },
    "en": {"title_base": "Cantata Tour", "caption": "Maharashtra", "tab_notice": "Notice", "tab_map": "Tour Route",
           "map_title": "View Route", "add_city": "Add City", "password": "Password", "login": "Login",
           "logout": "Logout", "wrong_pw": "Wrong password.", "select_city": "Select City", "venue": "Venue",
           "seats": "Expected Attendance", "note": "Notes", "google_link": "Google Maps Link",
           "indoor": "Indoor", "outdoor": "Outdoor", "register": "Register", "edit": "Edit", "remove": "Remove",
           "date": "Registered On", "performance_date": "Performance Date", "cancel": "Cancel", "title_label": "Title",
           "content_label": "Content", "upload_image": "Upload Image", "upload_file": "Upload File", "submit": "Submit",
           "warning": "Please enter both title and content.", "file_download": "Download File", "pending": "TBD",
           "est_time": "{hours}h {mins}m", "new_notice_alert": "Hot new notice arrived!"}
}
_ = lambda key: LANG.get(st.session_state.lang, LANG["ko"]).get(key, key)

# --- 안전 파일명 헬퍼 ---
def _safe_filename(name):
    return re.sub(r'[^0-9a-zA-Z._-]', '_', name)

# --- JSON 헬퍼 ---
def load_json(f):
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file:
                return json.load(file)
    except:
        pass
    return []

def save_json(f, d):
    with open(f, "w", encoding="utf-8") as file:
        json.dump(d, file, ensure_ascii=False, indent=2)

# --- 하버신 거리 ---
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))

# --- 실제 교통 시간 (fallback 포함) ---
@st.cache_data(ttl=1800, show_spinner=False)
def get_real_travel_time(lat1, lon1, lat2, lon2):
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    try:
        if not api_key:
            raise ValueError("No API key - using haversine fallback")
        origin = f"{lat1},{lon1}"
        dest = f"{lat2},{lon2}"
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={dest}&mode=driving&key={api_key}"
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if data.get("status") == "OK":
            leg = data["routes"][0]["legs"][0]
            dist = leg["distance"]["value"] / 1000.0
            mins = int(leg["duration"]["value"] // 60)
            return dist, mins
    except Exception as e:
        # 디버그 출력 (Streamlit 로그)
        try:
            st.write(f"get_real_travel_time fallback: {e}")
        except:
            pass
    dist = haversine(lat1, lon1, lat2, lon2)
    mins = int(dist * 60 / 55)
    return dist, mins

# --- 기본 도시 (초기 파일) ---
DEFAULT_CITIES = [
    {"city": "Mumbai", "venue": "Gateway of India", "seats": "5000", "note": "인도 영화 수도", "google_link": "https://goo.gl/maps/abc123", "indoor": False, "lat": 19.0760, "lon": 72.8777, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Pune", "venue": "Shaniwar Wada", "seats": "3000", "note": "IT 허브", "google_link": "https://goo.gl/maps/def456", "indoor": True, "lat": 18.5204, "lon": 73.8567, "perf_date": None, "date": "11/07 02:01"},
    {"city": "Nagpur", "venue": "Deekshabhoomi", "seats": "2000", "note": "오렌지 도시", "google_link": "https://goo.gl/maps/ghi789", "indoor": False, "lat": 21.1458, "lon": 79.0882, "perf_date": None, "date": "11/07 02:01"}
]
if not os.path.exists(CITY_FILE):
    save_json(CITY_FILE, DEFAULT_CITIES)

# --- 공지 기능 (요청: 알림/사운드 비활성화) ---
def add_notice(title, content, img=None, file=None):
    # 파일 안전 저장
    img_path = None; file_path = None
    if img:
        img_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{_safe_filename(img.name)}")
        open(img_path, "wb").write(img.read())
    if file:
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{_safe_filename(file.name)}")
        open(file_path, "wb").write(file.read())
    notice = {"id": str(uuid.uuid4()), "title": title, "content": content, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M"), "image": img_path, "file": file_path}
    data = load_json(NOTICE_FILE)
    data.insert(0, notice)
    save_json(NOTICE_FILE, data)
    st.session_state.seen_notices = []
    st.session_state.new_notice = True
    st.session_state.active_tab = "공지"
    st.rerun()

def render_notices():
    # 요청에 따라 공지의 배너/사운드 모두 비활성화: 단순 목록만 표시
    data = load_json(NOTICE_FILE)
    for i, n in enumerate(data):
        with st.expander(f"{n.get('date','')} | {n.get('title','')}", expanded=False):
            st.markdown(n.get("content",""))
            if n.get("image") and os.path.exists(n["image"]):
                st.image(n["image"], use_container_width=True)
            if n.get("file") and os.path.exists(n["file"]):
                with open(n["file"], "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                st.markdown(f'<a href="data:file/octet-stream;base64,{b64}" download="{os.path.basename(n["file"])}">파일 다운로드</a>', unsafe_allow_html=True)
            if st.session_state.admin and st.button("삭제", key=f"del_notice_{i}"):
                data.pop(i); save_json(NOTICE_FILE, data); st.experimental_rerun()

# --- 사이드바 (간단) ---
with st.sidebar:
    lang_options = ["한국어", "English"]
    lang_map = {"한국어":"ko", "English":"en"}
    idx = 0 if st.session_state.lang == "ko" else 1
    selected = st.selectbox("언어", lang_options, index=idx)
    if lang_map[selected] != st.session_state.lang:
        st.session_state.lang = lang_map[selected]
        st.experimental_rerun()

    st.markdown("---")
    if not st.session_state.admin:
        pw = st.text_input(_("password"), type="password")
        if st.button(_("login")):
            if pw == st.session_state.pw:
                st.session_state.admin = True
                st.experimental_rerun()
            elif pw in ["0691", "0692"]:
                st.session_state.pw = "9000" if pw == "0691" else "0009"
                st.experimental_rerun()
            else:
                st.error(_("wrong_pw"))
    else:
        st.success("관리자 모드")
        if st.button(_("logout")):
            st.session_state.admin = False
            st.experimental_rerun()

# --- 탭 관리: expander 자동 접힘 로직 ---
# 사용자 요청: 다른 탭으로 이동하면 모든 expander는 닫힌 상태로 초기화
tab_notice_label = _("tab_notice")
tab_map_label = _("tab_map")
tab1, tab2 = st.tabs([tab_notice_label, tab_map_label])

# 탭 변경 감지: 이전 active_tab과 다르면 expander 상태 초기화
current_tab = tab_notice_label if tab1 else tab_map_label
# Streamlit 탭 API doesn't give event directly; we use a session var managed below when rendering tabs

# --- 지도 렌더러 (Leaflet) ---
def render_leaflet_map():
    st.subheader(_("map_title"))
    # 로드 도시 데이터
    raw_cities = load_json(CITY_FILE)
    # normalize perf_date to YYYY-MM-DD or None
    for city in raw_cities:
        pd = city.get("perf_date")
        if not pd or pd in ("", "None", "null"):
            city["perf_date"] = None
        else:
            try:
                # Accept already YYYY-MM-DD
                _ = datetime.strptime(pd, "%Y-%m-%d")
            except:
                city["perf_date"] = None

    cities = sorted(raw_cities, key=lambda x: x.get("perf_date") or "9999-12-31")

    if not cities:
        st.warning("도시 없음")
        return

    # Prepare data for JS
    # calculate distances & times for segments in Python to avoid too many API calls in JS
    segs = []
    for i in range(len(cities)-1):
        a = cities[i]; b = cities[i+1]
        dist_km, mins = get_real_travel_time(a['lat'], a['lon'], b['lat'], b['lon'])
        segs.append({
            "from": a["city"], "to": b["city"],
            "a_lat": a["lat"], "a_lon": a["lon"], "b_lat": b["lat"], "b_lon": b["lon"],
            "dist_km": round(dist_km,1), "mins": int(mins),
            "a_perf": a.get("perf_date"), "b_perf": b.get("perf_date")
        })

    payload = {
        "cities": cities,
        "segs": segs,
        "today": date.today().isoformat()
    }

    # Leaflet HTML template: draws markers, polylines, and puts rotated divIcons at midpoints with parallel angle.
    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
      <style>
        html,body,#map {{ height: 650px; margin:0; padding:0; }}
        .label-div {{
            background: rgba(231,76,60,0.9); color: white; padding:4px 8px; border-radius:4px;
            font-weight:600; font-size:12px; white-space:nowrap; transform-origin:center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.4);
        }}
        .label-div.dimmed {{
            background: rgba(231,76,60,0.45); color: rgba(255,255,255,0.8);
        }}
      </style>
      <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    </head>
    <body>
      <div id="map"></div>
      <script>
        const payload = {json.dumps(payload)};
        const map = L.map('map').setView([payload.cities[0].lat, payload.cities[0].lon], 6);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 18
        }}).addTo(map);

        function isPast(dateStr) {{
            if(!dateStr) return false;
            const d = new Date(dateStr);
            const today = new Date(payload.today);
            // if date < today -> past
            return d < today;
        }}

        // markers
        payload.cities.forEach((c,i)=>{
            const past = isPast(c.perf_date);
            const marker = L.circleMarker([c.lat, c.lon], {{
                radius: 8,
                color: past ? 'rgba(200,20,20,0.5)' : 'rgba(200,20,20,1)',
                fillColor: past ? 'rgba(200,20,20,0.4)' : 'rgba(231,76,60,1)',
                fillOpacity: past ? 0.45 : 1.0,
                weight: 1
            }}).addTo(map);
            const popup = `<b>${{c.city}}</b><br>${{c.perf_date || '미정'}}<br>${{c.venue || '—'}}<br>인원: ${{c.seats || '—'}}<br>${{c.note || '—'}}`;
            marker.bindPopup(popup);
        }});

        // segments + mid-labels
        payload.segs.forEach(s=>{
            const a = [s.a_lat, s.a_lon], b = [s.b_lat, s.b_lon];
            // determine if segment is 'past' based on the 'from' city perf_date being before today
            const fromCity = payload.cities.find(x=>x.city===s.from);
            const fromPast = fromCity && isPast(fromCity.perf_date);
            const opacity = fromPast ? 0.5 : 1.0; // past lines 50% opacity (더 흐리게)
            const line = L.polyline([a,b], {{color:'#e74c3c', weight:6, opacity:opacity}}).addTo(map);

            // midpoint
            const midLat = (s.a_lat + s.b_lat)/2;
            const midLon = (s.a_lon + s.b_lon)/2;

            // angle: compute bearing in degrees for rotation (approx)
            const dy = s.b_lat - s.a_lat;
            const dx = s.b_lon - s.a_lon;
            // atan2 returns radians; convert to degrees. Use lon/lat differences (works for small distances)
            let angle = Math.atan2(dx, dy) * (180/Math.PI);
            // create label text
            const hours = Math.floor(s.mins / 60);
            const mins = s.mins % 60;
            const timeStr = (hours ? hours + 'h ' + mins + 'm' : mins + 'm');
            const labelText = `${s.dist_km}km ${timeStr}`;

            // create DivIcon
            const div = L.divIcon({
                className: '',
                html: `<div class="label-div ${fromPast ? 'dimmed' : ''}" style="transform: rotate(${angle}deg);">${labelText}</div>`,
                iconSize: [100,20],
                iconAnchor: [50, 10]
            });
            L.marker([midLat, midLon], {icon: div, interactive:false}).addTo(map);
        });

        // fit bounds
        const allCoords = payload.cities.map(c=>[c.lat, c.lon]);
        map.fitBounds(allCoords, {{padding:[50,50]}});
      </script>
    </body>
    </html>
    """
    # render
    st.components.v1.html(leaflet_html, height=670, scrolling=True)

# --- 지도 탭과 공지 탭 렌더링, 그리고 expander 자동 닫힘 제어 ---
with tab1:
    # 탭이 클릭되면 active_tab을 업데이트하고 expander 상태 초기화
    if st.session_state.get("active_tab") != tab_notice_label:
        st.session_state.active_tab = tab_notice_label
        st.session_state.expanded = {}
    if st.session_state.admin:
        with st.form("notice_form", clear_on_submit=True):
            t = st.text_input(_("title_label"))
            c = st.text_area(_("content_label"))
            img = st.file_uploader(_("upload_image"), type=["png","jpg","jpeg"])
            f = st.file_uploader(_("upload_file"))
            if st.form_submit_button(_("submit")):
                if t.strip() and c.strip():
                    add_notice(t, c, img, f)
                else:
                    st.warning(_("warning"))
    render_notices()

with tab2:
    # 탭 변경 시 expander 초기화
    if st.session_state.get("active_tab") != tab_map_label:
        st.session_state.active_tab = tab_map_label
        st.session_state.expanded = {}
    render_leaflet_map()

# --- 도시 편집/추가 UI (관리자 전용, 별도 섹션) ---
if st.session_state.admin:
    st.markdown("---")
    st.subheader("관리자: 도시 추가/편집")
    data = load_json(CITY_FILE)
    cols = st.columns([1,1,2])
    with cols[0]:
        new_city_name = st.text_input("도시 이름 (영문)", value="")
    with cols[1]:
        new_lat = st.text_input("위도", value="")
        new_lon = st.text_input("경도", value="")
    with cols[2]:
        new_venue = st.text_input("공연장소", value="")
    if st.button("도시 추가 (임시)"):
        try:
            lat = float(new_lat); lon = float(new_lon)
            new_city = {"city": new_city_name, "venue": new_venue, "seats":"0", "note":"", "google_link":"", "indoor":True, "lat":lat, "lon":lon, "perf_date":None, "date": datetime.now(timezone("Asia/Kolkata")).strftime("%m/%d %H:%M")}
            data.append(new_city)
            save_json(CITY_FILE, data)
            st.success("도시 추가됨")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"위치 정보 오류: {e}")

# --- 끝 ---
