import streamlit as st
import pandas as pd


@st.cache_data
def load_data():
    scoring = pd.read_csv('output/scoring_result.csv')
    clustered = pd.read_csv('output/tour_clustered.csv')
    return scoring, clustered


def congestion_label(score):
    if score >= 0.7:
        return "🟢 한산", "#2ecc71"
    elif score >= 0.5:
        return "🟡 보통", "#f39c12"
    elif score >= 0.3:
        return "🟠 붐빔", "#e67e22"
    else:
        return "🔴 매우 붐빔", "#e74c3c"
