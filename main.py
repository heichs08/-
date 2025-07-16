import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time # 애니메이션 속도 제어를 위해 추가

# --- 페이지 설정 ---
st.set_page_config(
    page_title="중력 렌즈 시뮬레이션",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일링 (우주 배경 흰색, 인터페이스 흰색 유지) ---
st.markdown(
    """
    <style>
    .reportview-container {
        background: white; /* 전체 배경을 흰색으로 설정 */
    }
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    /* 시뮬레이션 캔버스 배경을 흰색으로 설정 */
    .stPlotlyChart {
        background: white;
        border-radius: 10px; /* 모서리를 둥글게 */
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* 그림자 효과 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌌 중력 렌즈 시뮬레이션")
st.write("블랙홀의 강력한 중력이 빛과 주변 행성에 어떻게 영향을 미치는지 시뮬레이션하고, 중력 렌즈에 의한 빛의 배율을 확인해보세요.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 변수 설정")

# 1. 블랙홀과 항성 사이의 거리 (km)
bh_star_distance_km = st.sidebar.slider(
    "블랙홀-광원(항성) 거리 (km)",
    min_value=15_000_000,
    max_value=20_000_000,
    value=17_500_000,
    step=100_000,
    help="블랙홀과 광원(항성) 중심 사이의 초기 거리입니다. 시뮬레이션 중 이 거리는 변화합니다."
)
st.sidebar.write(f"설정된 초기 거리: {bh_star_distance_km:,} km")

# 2. 외계행성 질량 (kg)
planet_mass_exponent = st.sidebar.slider(
    "외계행성 질량 지수 (10^X kg)",
    min_value
