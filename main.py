import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
import imageio # GIF 생성을 위해 추가
import io # 바이트 스트림 처리를 위해 추가

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
    min_value=23.0,
    max_value=25.0,
    value=24.0,
    step=0.1,
    help="행성의 질량을 10의 거듭제곱 형태로 설정합니다. (예: 24.0은 10^24 kg)"
)
planet_mass_kg = 10**planet_mass_exponent
st.sidebar.write(f"설정된 행성 질량: {planet_mass_kg:.2e} kg")

# 3. 행성과 항성 사이의 거리 (AU)
planet_star_distance_au = st.sidebar.slider(
    "행성과 항성 사이 거리 (AU)",
    min_value=0.5,
    max_value=1.0,
    value=0.8,
    step=0.01,
    help="행성이 항성을 공전하는 평균 거리입니다. 1 AU는 지구-태양 거리와 같습니다."
)
au_to_km = 149_597_870.7 # 1 AU in km
planet_star_distance_km = planet_star_distance_au * au_to_km
st.sidebar.write(f"설정된 거리: {planet_star_distance_au:.2f} AU ({planet_star_distance_km:,.0f} km)")

animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by AI Assistant")

# --- 시뮬레이션 영역 ---
st.header("시뮬레이션")
simulation_placeholder = st.empty() # 애니메이션 프레임을 표시할 곳

# GIF 표시를 위한 Placeholder
gif_placeholder = st.empty()

# --- 그래프 영역 ---
st.header("데이터 그래프")
st.subheader("행성 운동 특성")
planet_graph_placeholder = st.empty()
st.subheader("관측된 빛의 배율 변화")
magnification_graph_placeholder = st.empty()

# --- 시뮬레이션 로직 함수 ---
def run_simulation(bh_star_distance_km, planet_mass_kg, planet_star_distance_au, animation_speed):
    num_frames = 400 # 프레임 수 증가 (애니메이션 부드럽게)
    time_points = np.arange(num_frames)
    
    # 시뮬레이션 스케일 조정 (1000만 km 단위를 1 단위로 매핑)
    scale_factor = 1e-7
    bh_star_distance
