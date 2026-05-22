import streamlit as st
import pandas as pd
from utils import congestion_label


def render_cards(recs):
    st.subheader("✨ 대안 추천")
    for _, row in recs.iterrows():
        c_label, c_color = congestion_label(row['congestion_score'])
        with st.container(border=True):
            img_url = row.get('image_url', '')
            img_col, info_col = st.columns([1, 2])
            with img_col:
                if pd.notna(img_url) and str(img_url).startswith('http'):
                    st.image(img_url, use_container_width=True)
            with info_col:
                st.markdown(f"**{int(row['rank'])}위. {row['name']}**")
                st.markdown(
                    f"<span style='color:{c_color}'>{c_label}</span> &nbsp; **점수: {row['final_score']:.2f}**",
                    unsafe_allow_html=True
                )
                st.caption(row.get('address', ''))
                st.caption(f"테마: {row.get('cluster_theme', '-')} | 거리: {row['dist_km']:.1f}km")
