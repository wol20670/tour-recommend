# app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from math import radians, sin, cos, sqrt, atan2
import numpy as np

# ── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="오늘 어디 갈까 🗺️",
    page_icon="🗺️",
    layout="wide"
)

# ── 데이터 로드 (캐싱) ───────────────────────────────────────
@st.cache_data
def load_data():
    scoring = pd.read_csv('output/scoring_result.csv')
    clustered = pd.read_csv('output/tour_clustered.csv')
    return scoring, clustered

scoring_df, clustered_df = load_data()

# 검색 가능한 관광지 목록 (origin 기준)
origin_list = sorted(scoring_df['origin_name'].unique().tolist())

# ── 혼잡도 텍스트/색상 ───────────────────────────────────────
def congestion_label(score):
    if score >= 0.7:
        return "🟢 한산", "#2ecc71"
    elif score >= 0.5:
        return "🟡 보통", "#f39c12"
    elif score >= 0.3:
        return "🟠 붐빔", "#e67e22"
    else:
        return "🔴 매우 붐빔", "#e74c3c"

# ── 사이드바 ─────────────────────────────────────────────────
st.sidebar.title("🗺️ 오늘 어디 갈까")
st.sidebar.markdown("미디어로 유명해진 관광지, 대신 갈 만한 곳을 추천해드려요.")
st.sidebar.markdown("---")

search_input = st.sidebar.text_input("관광지 이름 검색", placeholder="예: 경복궁, 해운대...")

# 입력값으로 필터링
if search_input:
    filtered = [x for x in origin_list if search_input in x]
else:
    filtered = origin_list

if not filtered:
    st.sidebar.warning("검색 결과가 없습니다.")
    selected = ""
elif len(filtered) == 1:
    selected = filtered[0]
else:
    selected = st.sidebar.selectbox(
        "관광지 선택",
        options=[""] + filtered,
        index=0
    )

top_n = st.sidebar.slider("추천 개수", min_value=3, max_value=10, value=5)

# ── 메인 ─────────────────────────────────────────────────────
st.title("🗺️ 오늘 어디 갈까?")
st.markdown("붐비는 관광지 대신, **같은 테마의 한산한 곳**을 추천해드려요.")

if not selected:
    st.info("👈 왼쪽에서 목적지 관광지를 선택해주세요.")
    st.stop()

# 원점 관광지 정보
origin_info = clustered_df[clustered_df['name'] == selected]
if origin_info.empty:
    st.error("관광지 정보를 찾을 수 없습니다.")
    st.stop()

origin = origin_info.iloc[0]

# 추천 결과
recs = scoring_df[scoring_df['origin_name'] == selected].head(top_n)

# ── 원점 정보 표시 ───────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader(f"📍 {selected}")
    st.caption(origin.get('address', ''))

with col2:
    c_score = origin.get('congestion_score', 0.5)
    label, color = congestion_label(c_score)
    st.metric("현재 혼잡도", label)

with col3:
    theme = origin.get('cluster_theme', '-')
    st.metric("테마", theme)

st.markdown("---")

# ── 추천 결과 + 지도 ─────────────────────────────────────────
col_cards, col_map = st.columns([1, 1.5])

with col_cards:
    st.subheader("✨ 대안 추천")
    for _, row in recs.iterrows():
        c_label, c_color = congestion_label(row['congestion_score'])
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**{int(row['rank'])}위. {row['name']}**")
                st.caption(row.get('address', ''))
                st.caption(f"테마: {row.get('cluster_theme', '-')} | 거리: {row['dist_km']:.1f}km")
            with c2:
                st.markdown(f"<span style='color:{c_color}'>{c_label}</span>", unsafe_allow_html=True)
                st.markdown(f"**점수: {row['final_score']:.2f}**")

with col_map:
    st.subheader("🗺️ 지도")
    
    # 지도 중심: 원점
    o_lat = float(origin['latitude'])
    o_lon = float(origin['longitude'])
    
    m = folium.Map(location=[o_lat, o_lon], zoom_start=12)
    
    # 원점 마커 (빨강)
    folium.Marker(
        location=[o_lat, o_lon],
        tooltip=folium.Tooltip(f"📍 {selected}", sticky=False),
        popup=folium.Popup(f"<b>{selected}</b><br>{origin.get('address', '')}", max_width=200),
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # 추천 마커 (파랑)
    for _, row in recs.iterrows():
        if pd.notna(row['latitude']) and pd.notna(row['longitude']):
            folium.Marker(
                location=[float(row['latitude']), float(row['longitude'])],
                tooltip=folium.Tooltip(f"{int(row['rank'])}위. {row['name']}", sticky=False),
                popup=folium.Popup(
                    f"<b>{row['name']}</b><br>"
                    f"거리: {row['dist_km']:.1f}km<br>"
                    f"테마: {row.get('cluster_theme', '-')}<br>"
                    f"점수: {row['final_score']:.2f}",
                    max_width=200
                ),
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(m)

    st_folium(m, use_container_width=True, height=500)

# ── 상세 테이블 ──────────────────────────────────────────────
with st.expander("📊 상세 스코어 보기"):
    display_cols = ['rank','name','dist_km','congestion_score',
                    'distance_score','theme_score','final_score','cluster_theme']
    st.dataframe(recs[display_cols].set_index('rank'), use_container_width=True)