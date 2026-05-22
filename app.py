import streamlit as st
from utils import load_data, congestion_label
from components.cards import render_cards
from components.map_view import render_map

st.set_page_config(
    page_title="오늘 어디 갈까 🗺️",
    page_icon="🗺️",
    layout="wide"
)

scoring_df, clustered_df = load_data()
origin_list = sorted(scoring_df['origin_name'].unique().tolist())

# ── 사이드바 ─────────────────────────────────────────────────
st.sidebar.title("🗺️ 오늘 어디 갈까")
st.sidebar.markdown("미디어로 유명해진 관광지, 대신 갈 만한 곳을 추천해드려요.")
st.sidebar.markdown("---")

search_input = st.sidebar.text_input("관광지 이름 검색", placeholder="예: 경복궁, 해운대...")

filtered = [x for x in origin_list if search_input in x] if search_input else origin_list

if not filtered:
    st.sidebar.warning("검색 결과가 없습니다.")
    selected = ""
elif len(filtered) == 1:
    selected = filtered[0]
else:
    selected = st.sidebar.selectbox("관광지 선택", options=[""] + filtered, index=0)

top_n = st.sidebar.slider("추천 개수", min_value=3, max_value=10, value=5)

# ── 메인 ─────────────────────────────────────────────────────
st.title("🗺️ 오늘 어디 갈까?")
st.markdown("붐비는 관광지 대신, **같은 테마의 한산한 곳**을 추천해드려요.")

if not selected:
    st.info("👈 왼쪽에서 목적지 관광지를 선택해주세요.")
    st.stop()

origin_info = clustered_df[clustered_df['name'] == selected]
if origin_info.empty:
    st.error("관광지 정보를 찾을 수 없습니다.")
    st.stop()

origin = origin_info.iloc[0]
recs = scoring_df[scoring_df['origin_name'] == selected].head(top_n)

# ── 원점 정보 ────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"📍 {selected}")
    st.caption(origin.get('address', ''))
with col2:
    label, _ = congestion_label(origin.get('congestion_score', 0.5))
    st.metric("현재 혼잡도", label)
with col3:
    st.metric("테마", origin.get('cluster_theme', '-'))

st.markdown("---")

# ── 추천 카드 + 지도 ─────────────────────────────────────────
col_cards, col_map = st.columns([1, 1.5])
with col_cards:
    render_cards(recs)
with col_map:
    render_map(origin, selected, recs)

# ── 상세 테이블 ──────────────────────────────────────────────
with st.expander("📊 상세 스코어 보기"):
    display_cols = ['rank', 'name', 'dist_km', 'congestion_score',
                    'distance_score', 'theme_score', 'final_score', 'cluster_theme']
    st.dataframe(recs[display_cols].set_index('rank'), use_container_width=True)
