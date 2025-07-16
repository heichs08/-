import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import time # 애니메이션 속도 제어를 위해 추가

# --- 페이지 설정 ---
st.set_page_config(
    page_title="중력 렌즈 시뮬레이션",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일링 (하얀색 인터페이스, 검은 우주 배경) ---
st.markdown(
    """
    <style>
    .reportview-container {
        background: white; # 전체 배경을 흰색으로 설정
    }
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌌 중력 렌즈 시뮬레이션")
st.write("블랙홀의 강력한 중력이 빛과 주변 행성에 어떻게 영향을 미치는지 시뮬레이션하고, 중력 렌즈에 의한 빛의 배율을 확인해보세요.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 설정")
# 기존 변수 설정 유지 (이전 답변에서 제공된 변수들)
bh_star_distance_km = st.sidebar.slider(
    "블랙홀-항성 거리 (km)",
    min_value=15_000_000,
    max_value=20_000_000,
    value=17_500_000,
    step=100_000,
    help="블랙홀과 광원(항성) 중심 사이의 거리입니다."
)

planet_mass_exponent = st.sidebar.slider(
    "외계행성 질량 지수 (10^X kg)",
    min_value=23.0,
    max_value=25.0,
    value=24.0,
    step=0.1,
    help="행성의 질량을 10의 거듭제곱 형태로 설정합니다."
)
planet_mass_kg = 10**planet_mass_exponent

planet_star_distance_au = st.sidebar.slider(
    "행성-항성 거리 (AU)",
    min_value=0.5,
    max_value=1.0,
    value=0.8,
    step=0.01,
    help="행성이 항성을 공전하는 평균 거리입니다. 1 AU는 지구-태양 거리와 같습니다."
)
au_to_km = 149_597_870.7

animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)

# --- 시뮬레이션 영역 (검은 배경) ---
st.header("시뮬레이션")
simulation_placeholder = st.empty()

# --- 그래프 영역 ---
st.header("데이터 그래프")
st.subheader("행성 운동 특성")
planet_graph_placeholder = st.empty()
st.subheader("중력 렌즈 배율 변화")
magnification_graph_placeholder = st.empty()


# --- 시뮬레이션 로직 함수 ---
def run_simulation(bh_star_distance_km, planet_mass_kg, planet_star_distance_au, animation_speed):
    num_frames = 200 # 프레임 수 증가 (더 부드러운 애니메이션)
    theta = np.linspace(0, 2 * np.pi, num_frames)

    # 블랙홀 위치 (중심)
    bh_x, bh_y = 0, 0

    # 광원(항성) 위치 (임의로 시뮬레이션 평면에 고정)
    # 실제로는 이 광원이 블랙홀 뒤에 있고, 관측자와 블랙홀 사이의 정렬에 따라 왜곡됩니다.
    # 여기서는 시뮬레이션의 '중심 광원'이라고 가정합니다.
    source_x, source_y = 5, 0 # 블랙홀에서 약간 떨어진 광원

    # 행성 위치 (공전 시뮬레이션 - 항성 주변 공전으로 간주)
    # 여기서는 간단히 원형 궤도로 표현합니다.
    planet_orbit_radius_sim = 4 # 시뮬레이션 스케일에 맞게 조정
    planet_x = planet_orbit_radius_sim * np.cos(theta)
    planet_y = planet_orbit_radius_sim * np.sin(theta)

    # 중력 렌즈 효과를 위한 배경 별들 (랜덤하게 분포)
    num_stars = 500
    star_x = np.random.uniform(-10, 10, num_stars)
    star_y = np.random.uniform(-10, 10, num_stars)

    # --- 그래프 데이터 생성 (개념적인 모델) ---
    time_points = np.arange(num_frames)
    
    # 1. 행성 운동 특성 (에너지, 거리)
    # 실제 물리 시뮬레이션에 기반하여 계산되어야 함
    energy_data = np.sin(time_points / 20 * np.pi) * 5 + 15 # 가상 에너지 변화
    distance_data = planet_orbit_radius_sim + np.cos(time_points / 30 * np.pi) * 0.5 # 가상 거리 변화 (약간의 진동)

    # 2. 중력 렌즈 배율 데이터
    # 광원이 블랙홀에 얼마나 가까워지는지에 따라 배율이 변한다고 가정
    # 예: 광원과 블랙홀 간의 '정렬'을 나타내는 값 (0에 가까울수록 정렬됨)
    # 실제 렌즈 배율 공식: A = (y^2 + 2) / (y * sqrt(y^2 + 4)) where y is the dimensionless impact parameter
    # 여기서는 광원의 x 위치를 기준으로 간단한 배율 곡선을 만듭니다.
    # 광원의 X축 위치가 0에 가까워질수록 배율이 높아지게 (블랙홀에 가까워진다고 가정)
    
    # 가상의 광원 상대 위치 (시간에 따라 변한다고 가정)
    # 예를 들어, 광원이 블랙홀을 가로지르는 것처럼 시뮬레이션
    source_relative_pos = np.sin(time_points / (num_frames / 4) * np.pi) * 5 # -5에서 5까지 변동
    
    # 중력 렌즈 배율 계산 (개념적인 함수)
    # y = source_relative_pos. 작은 y 값은 큰 배율을 의미
    # y가 0에 가까워질수록 (렌즈 중심에 가까워질수록) 배율이 급격히 증가
    epsilon = 0.5 # 0으로 나누는 것을 방지하고 피크를 조절
    magnification_data = 1 + (1 / (np.abs(source_relative_pos) + epsilon)) * 10 # 1에서 시작하여 피크 형성

    frames = []
    for i in range(num_frames):
        fig_sim = go.Figure()

        # 검은색 배경 설정
        fig_sim.update_layout(
            paper_bgcolor='black',
            plot_bgcolor='black',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 10]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-10, 10]),
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=600 # 시뮬레이션 캔버스 높이
        )

        # 배경 별 (흰색 점)
        fig_sim.add_trace(go.Scatter(
            x=star_x, y=star_y,
            mode='markers',
            marker=dict(size=2, color='white'),
            name='Stars'
        ))

        # 보라빛 블랙홀
        fig_sim.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y],
            mode='markers',
            marker=dict(
                size=np.cbrt(bh_star_distance_km / 1e6) * 5, # 거리 기반으로 크기 조정
                color='purple',
                opacity=0.7,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 광원 (항성)
        fig_sim.add_trace(go.Scatter(
            x=[source_x], y=[source_y],
            mode='markers',
            marker=dict(
                size=15 + magnification_data[i]*0.5, # 배율에 따라 크기 변화 (시각적 효과)
                color='yellow',
                opacity=0.9,
                line=dict(width=0),
                symbol='star'
            ),
            name='Source Star'
        ))

        # 행성 공전
        fig_sim.add_trace(go.Scatter(
            x=[planet_x[i]], y=[planet_y[i]],
            mode='markers',
            marker=dict(size=10, color='orange'), # 행성 색상
            name='Exoplanet'
        ))

        # 프레임 저장
        frames.append(fig_sim)

    # --- 그래프 시각화 (Plotly) ---
    fig_planet_props = make_planet_properties_graph(time_points, energy_data, distance_data)
    fig_magnification = make_magnification_graph(time_points, magnification_data)

    return frames, fig_planet_props, fig_magnification

def make_planet_properties_graph(time, energy, distance):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=time, y=energy, mode='lines', name='에너지 변화',
                             line=dict(color='lightgreen', width=2)))
    fig.add_trace(go.Scatter(x=time, y=distance, mode='lines', name='거리 변화',
                             line=dict(color='orange', width=2)))

    fig.update_layout(
        title="행성 운동 특성",
        xaxis_title="시간 (프레임)",
        yaxis_title="값",
        template="plotly_white",
        hovermode="x unified",
        height=300 # 그래프 높이 조절
    )
    return fig

def make_magnification_graph(time, magnification):
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=time, y=magnification, mode='lines', name='배율',
                             line=dict(color='cyan', width=2)))

    fig.update_layout(
        title="중력 렌즈에 의한 빛의 배율 변화",
        xaxis_title="시간 (프레임)",
        yaxis_title="배율",
        template="plotly_white",
        hovermode="x unified",
        height=300, # 그래프 높이 조절
        yaxis_range=[0, np.max(magnification)*1.2] # y축 범위 자동 조절
    )
    return fig


# --- 시뮬레이션 실행 및 업데이트 ---
if st.button("시뮬레이션 시작"):
    frames, fig_planet_props, fig_magnification = run_simulation(
        bh_star_distance_km, planet_mass_kg, planet_star_distance_au, animation_speed
    )

    # 시뮬레이션 애니메이션
    for i, frame in enumerate(frames):
        with simulation_placeholder:
            st.plotly_chart(frame, use_container_width=True, config={'displayModeBar': False})
        time.sleep(0.1 / animation_speed) # 속도에 따라 지연 시간 조절

    # 행성 운동 특성 그래프 표시
    with planet_graph_placeholder:
        st.plotly_chart(fig_planet_props, use_container_width=True)

    # 중력 렌즈 배율 변화 그래프 표시
    with magnification_graph_placeholder:
        st.plotly_chart(fig_magnification, use_container_width=True)
