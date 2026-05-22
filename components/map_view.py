import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


def render_map(origin, selected, recs):
    st.subheader("🗺️ 지도")

    o_lat = float(origin['latitude'])
    o_lon = float(origin['longitude'])

    m = folium.Map(location=[o_lat, o_lon], zoom_start=12)

    folium.Marker(
        location=[o_lat, o_lon],
        tooltip=folium.Tooltip(f"📍 {selected}", sticky=False),
        popup=folium.Popup(f"<b>{selected}</b><br>{origin.get('address', '')}", max_width=200),
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)

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
