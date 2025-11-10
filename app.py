# app.py — Cantata-app (최신 완성본)
import streamlit as st
from datetime import datetime
import folium
from streamlit_folium import st_folium
from folium.plugins import AntPath
from pytz import timezone
import json, os, uuid, base64, random

# -----------------------------
# 1. 기본 설정
# -----------------------------
st.set_page_config(page_title="칸타타 투어 2025", layout="wide")

# 파일 경로
NOTICE_FILE = "notice.json"
TOUR_FILE = "tour_schedule.json"
POST_FILE = "user_posts.json"
CITIES_FILE = "cities.json"

# 타임존 설정 (인도 뭄바이)
tz = timezone("Asia/Kolkata")

# -----------------------------
# 2. 데이터 로드 & 저장 함수
# -----------------------------
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return default
    else:
        return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -----------------------------
# 3. 데이터 로드
# -----------------------------
notices = load_json(NOTICE_FILE, [])
tour_schedule = load_json(TOUR_FILE, [])
posts = load_json(POST_FILE, [])
cities = load_json(CITIES_FILE, {})

# -----------------------------
# 4. 관리자 모드
# -----------------------------
st.sidebar.header("관리자 설정")
is_admin = st.sidebar.checkbox("관리자 모드")
if is_admin:
    admin_pass = st.sidebar.text_input("비밀번호", type="password")
    if admin_pass == "cantata2025":
        st.sidebar.success("관리자 인증됨 ✅")
        admin_mode = True
    else:
        st.sidebar.warning("비밀번호를 입력하세요")
        admin_mode = False
else:
    admin_mode = False

# -----------------------------
# 5. 상단 로고 및 제목
# -----------------------------
st.markdown(
    "<h1 style='text-align:center; color:#D90429;'>🎵 칸타타 투어 2025</h1>",
    unsafe_allow_html=True
)

# -----------------------------
# 6. 공지사항 섹션
# -----------------------------
st.subheader("📢 공지사항")
if len(notices) == 0:
    st.info("등록된 공지가 없습니다.")
else:
    for i, n in enumerate(sorted(notices, key=lambda x: x["time"], reverse=True)):
        date = datetime.fromisoformat(n["time"]).astimezone(tz)
        label = f"🕒 {date.strftime('%m/%d %H:%M')}  |  {n['title']}"
        with st.expander(label):
            st.markdown(n["content"])

if admin_mode:
    st.markdown("---")
    st.markdown("### ✍️ 새 공지 등록")
    with st.form("add_notice"):
        title = st.text_input("공지 제목")
        content = st.text_area("공지 내용")
        submitted = st.form_submit_button("등록")
        if submitted:
            notices.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "time": datetime.now(tz).isoformat()
            })
            save_json(NOTICE_FILE, notices)
            st.success("공지 등록 완료!")
            st.rerun()

# -----------------------------
# 7. 투어 일정 & 지도 표시
# -----------------------------
st.markdown("---")
st.subheader("🗺️ 투어 경로 보기")

if len(tour_schedule) == 0:
    st.info("등록된 투어 일정이 없습니다.")
else:
    # 지도 초기화 (첫 도시 기준)
    first_city = list(cities.keys())[0] if cities else "Mumbai"
    start_lat = cities.get(first_city, {}).get("lat", 19.076)
    start_lon = cities.get(first_city, {}).get("lon", 72.8777)
    fmap = folium.Map(location=[start_lat, start_lon], zoom_start=6)

    # 도시 경로 그리기
    coords = []
    for t in tour_schedule:
        city = t["city"]
        info = cities.get(city)
        if info:
            lat, lon = info["lat"], info["lon"]
            coords.append((lat, lon))
            popup_html = f"<b>{city}</b><br>{t['date']}<br>가능성: {t.get('possibility','-')}"
            folium.Marker([lat, lon], popup=popup_html).add_to(fmap)

    if len(coords) >= 2:
        AntPath(coords, color="#D90429", delay=800).add_to(fmap)

    st_data = st_folium(fmap, width=1000, height=500)

# -----------------------------
# 8. 관리자: 도시 추가/수정
# -----------------------------
if admin_mode:
    st.markdown("---")
    st.subheader("🏙️ 도시 관리")

    with st.expander("도시 추가"):
        with st.form("add_city"):
            city_name = st.text_input("도시명")
            lat = st.number_input("위도", value=19.0, step=0.001)
            lon = st.number_input("경도", value=73.0, step=0.001)
            add_btn = st.form_submit_button("도시 추가")

            if add_btn:
                if city_name in cities:
                    st.warning("이미 등록된 도시입니다.")
                else:
                    cities[city_name] = {"lat": lat, "lon": lon}
                    save_json(CITIES_FILE, cities)
                    st.success(f"{city_name} 추가 완료!")
                    st.rerun()

# -----------------------------
# 9. 관리자: 투어 일정 관리
# -----------------------------
if admin_mode:
    st.markdown("---")
    st.subheader("🎼 투어 일정 관리")

    with st.form("add_tour"):
        city_sel = st.selectbox("도시 선택", list(cities.keys()))
        date = st.date_input("날짜")
        possibility = st.text_input("가능성 (%) 또는 설명")
        add_tour_btn = st.form_submit_button("일정 추가")

        if add_tour_btn:
            new_entry = {
                "city": city_sel,
                "date": date.strftime("%Y-%m-%d"),
                "possibility": possibility
            }
            tour_schedule.append(new_entry)
            save_json(TOUR_FILE, tour_schedule)
            st.success("투어 일정이 추가되었습니다.")
            st.rerun()

# -----------------------------
# 10. 사용자 게시판
# -----------------------------
st.markdown("---")
st.subheader("💬 공연 후기 / 응원 남기기")

for p in sorted(posts, key=lambda x: x["time"], reverse=True):
    date = datetime.fromisoformat(p["time"]).astimezone(tz)
    st.markdown(f"**{p['name']}** · {date.strftime('%m/%d %H:%M')}")
    st.markdown(p["content"])
    st.markdown("---")

with st.form("user_post"):
    name = st.text_input("이름")
    content = st.text_area("내용")
    submitted = st.form_submit_button("등록")
    if submitted:
        posts.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "content": content,
            "time": datetime.now(tz).isoformat()
        })
        save_json(POST_FILE, posts)
        st.success("등록 완료!")
        st.rerun()

# -----------------------------
# 끝
# -----------------------------
