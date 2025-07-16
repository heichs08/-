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

# --- 그래프 영역 ---
st.header("데이터 그래프")
st.subheader("행성 운동 특성")
planet_graph_placeholder = st.empty()
st.subheader("관측된 빛의 배율 변화")
magnification_graph_placeholder = st.empty()

# --- 시뮬레이션 로직 함수 ---
def run_simulation(bh_star_distance_km, planet_mass_kg, planet_star_distance_au, animation_speed):
    num_frames = 400 # 프레임 수
    time_points = np.arange(num_frames)
    
    # 시뮬레이션 스케일 조정 (1000만 km 단위를 1 단위로 매핑)
    scale_factor = 1e-7
    bh_star_distance_scaled = bh_star_distance_km * scale_factor

    # 블랙홀 위치 (중심)
    bh_x, bh_y = 0, 0

    # 광원(항성) 경로: 블랙홀을 지나가도록 설정
    source_x_path = np.linspace(-bh_star_distance_scaled * 0.8, bh_star_distance_scaled * 0.8, num_frames)
    source_y_path = np.zeros(num_frames)

    # 행성 공전: 항성 주위를 공전하도록 설정
    planet_orbit_radius_sim = planet_star_distance_au * 0.1
    
    magnification_data_list = [] # 중력 렌즈 배율 데이터 저장

    # 별의 고정된 위치를 미리 생성 (애니메이션 중 움직이지 않도록)
    num_stars = 1000
    star_x_bg = np.random.uniform(-bh_star_distance_scaled * 1.5, bh_star_distance_scaled * 1.5, num_stars)
    star_y_bg = np.random.uniform(-bh_star_distance_scaled * 1.5, bh_star_distance_scaled * 1.5, num_stars)
    star_sizes = np.random.uniform(1, 4, num_stars)
    star_opacities = np.random.uniform(0.5, 1.0, num_stars)

    for i in range(num_frames):
        current_source_x = source_x_path[i]
        current_source_y = source_y_path[i]

        # 행성 위치 (항성을 중심으로 공전)
        planet_angle = 2 * np.pi * (i / (num_frames / 2))
        planet_x = current_source_x + planet_orbit_radius_sim * np.cos(planet_angle)
        planet_y = current_source_y + planet_orbit_radius_sim * np.sin(planet_angle)

        # 중력 렌즈 배율 계산
        impact_parameter = np.abs(current_source_x) + 1e-5
        magnification = 1 + (1 / impact_parameter) * 10.0
        magnification = min(magnification, 70.0)
        magnification_data_list.append(magnification)

        fig_sim = go.Figure()

        # 흰색 배경 설정 (시뮬레이션 캔버스)
        fig_sim.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-bh_star_distance_scaled * 1.2, bh_star_distance_scaled * 1.2]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-bh_star_distance_scaled * 1.2, bh_star_distance_scaled * 1.2]),
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=600
        )

        # 배경 별
        fig_sim.add_trace(go.Scatter(
            x=star_x_bg, y=star_y_bg,
            mode='markers',
            marker=dict(size=star_sizes, color='lightgray', opacity=star_opacities),
            name='Stars'
        ))

        # 블랙홀의 아크리션 디스크 (강착원반)
        for k in range(5, 0, -1):
            disk_radius = np.cbrt(bh_star_distance_km / 1e6) * k * 0.5 / 5
            color_val = int(255 * (k / 5))
            fig_sim.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=bh_x - disk_radius, y0=bh_y - disk_radius,
                              x1=bh_x + disk_radius, y1=bh_y + disk_radius,
                              fillcolor=f'rgba(255, {color_val}, 0, {0.1 + k*0.1})',
                              line_width=0,
                              layer="below")

        # 보라빛 블랙홀 (중앙)
        fig_sim.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y],
            mode='markers',
            marker=dict(
                size=np.cbrt(bh_star_distance_km / 1e6) * 5,
                color='purple',
                opacity=0.8,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 광원 (항성)
        fig_sim.add_trace(go.Scatter(
            x=[current_source_x], y=[current_source_y],
            mode='markers',
            marker=dict(
                size=15 + (magnification - 1) * 0.5,
                color='gold',
                opacity=0.9,
                line=dict(width=0),
                symbol='star'
            ),
            name='Source Star'
        ))

        # 행성 공전
        fig_sim.add_trace(go.Scatter(
            x=[planet_x], y=[planet_y],
            mode='markers',
            marker=dict(size=10, color='deepskyblue'),
            name='Exoplanet'
        ))
        
        # 실시간 시뮬레이션 표시
        with simulation_placeholder:
            st.plotly_chart(fig_sim, use_container_width=True, config={'displayModeBar': False})
        time.sleep(0.05 / animation_speed) # 속도 조절

    # --- 그래프 데이터 준비 ---
    energy_data = np.sin(time_points / 20 * np.pi) * 5 + 15
    distance_data = planet_orbit_radius_sim + np.cos(time_points / 30 * np.pi) * 0.05

    fig_planet_props = make_planet_properties_graph(time_points, energy_data, distance_data)
    fig_magnification = make_magnification_graph(time_points, np.array(magnification_data_list))

    return fig_planet_props, fig_magnification

def make_planet_properties_graph(time, energy, distance):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=energy, mode='lines', name='에너지 변화', line=dict(color='lightgreen', width=2)))
    fig.add_trace(go.Scatter(x=time, y=distance, mode='lines', name='거리 변화', line=dict(color='orange', width=2)))
    fig.update_layout(
        title="행성 운동 특성",
        xaxis_title="시간 (프레임)",
        yaxis_title="값",
        template="plotly_white",
        hovermode="x unified",
        height=300
    )
    return fig

def make_magnification_graph(time, magnification):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=magnification, mode='lines', name='배율', line=dict(color='crimson', width=2)))
    fig.update_layout(
        title="관측된 빛의 배율 변화 (중력 렌즈 효과)",
        xaxis_title="시간 (프레임)",
        yaxis_title="배율",
        template="plotly_white",
        hovermode="x unified",
        height=300,
        yaxis_range=[0, np.max(magnification)*1.1]
    )
    return fig

# --- 시뮬레이션 실행 및 업데이트 ---
if st.button("시뮬레이션 시작"):
    with st.spinner("시뮬레이션 실행 중..."):
        # GIF 관련 반환값과 로직을 제거하고, 그래프만 반환하도록 변경
        fig_planet_props, fig_magnification = run_simulation(
            bh_star_distance_km, planet_mass_kg, planet_star_distance_au, animation_speed
        )
        
    st.success("시뮬레이션 완료!")
    
    # 행성 운동 특성 그래프 표시
    with planet_graph_placeholder:
        st.plotly_chart(fig_planet_props, use_container_width=True)

    # 중력 렌즈 배율 변화 그래프 표시
    with magnification_graph_placeholder:
        st.plotly_chart(fig_magnification, use_container_width=True)
