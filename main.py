import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time

# --- 페이지 설정 ---
st.set_page_config(
    page_title="미세중력렌즈 시뮬레이션",
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

st.title("🌟 미세중력렌즈 시뮬레이션 (외계 행성 효과)")
st.write("외계 행성이 배경 항성의 빛을 어떻게 증폭시키는지 시뮬레이션합니다.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 변수 설정")

# 미세중력렌즈에 더 적합한 변수로 변경하거나 기존 변수 의미 재정의
# 이전 '블랙홀-항성 거리'는 이제 '렌즈-광원 시스템의 스케일'로 사용
system_scale_km = st.sidebar.slider(
    "시스템 스케일 (백만 km 단위)",
    min_value=10,
    max_value=100,
    value=50,
    step=1,
    help="시뮬레이션 공간의 대략적인 크기를 설정합니다. (단위: 백만 km)"
)
system_scale_au = system_scale_km * 1e6 / 149_597_870.7 # km를 AU로 변환

# 외계행성 (렌즈) 질량
planet_mass_exponent = st.sidebar.slider(
    "외계행성 (렌즈) 질량 지수 (10^X kg)",
    min_value=23.0,
    max_value=27.0, # 행성 질량 범위 확장 (갈색 왜성 등)
    value=24.5,
    step=0.1,
    help="렌즈 역할을 하는 행성의 질량을 10의 거듭제곱 형태로 설정합니다."
)
planet_lens_mass_kg = 10**planet_mass_exponent
st.sidebar.write(f"설정된 행성 질량: {planet_lens_mass_kg:.2e} kg")

# 외계행성 (렌즈)의 항성(광원) 앞 통과 경로의 '충격 매개변수' (얼마나 중심을 지나가는지)
impact_parameter_scaled = st.sidebar.slider(
    "통과 경로 이탈 정도 (0:중심, 1:가장자리)",
    min_value=0.0,
    max_value=1.0,
    value=0.1, # 0에 가까울수록 밝기 피크가 높아짐
    step=0.01,
    help="렌즈 행성이 광원 항성의 중심을 얼마나 벗어나서 지나가는지 설정합니다. 0에 가까울수록 밝기 증폭이 큽니다."
)

animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)


# --- 시뮬레이션 영역 ---
st.header("시뮬레이션")
simulation_placeholder = st.empty()

# --- 그래프 영역 ---
st.header("데이터 그래프")
# 행성 운동 특성 그래프는 미세중력렌즈 맥락에서는 덜 중요하므로, 필요시 추가
# st.subheader("행성 운동 특성")
# planet_graph_placeholder = st.empty()
st.subheader("외계 행성에 의한 항성의 밝기 변화 (미세중력렌즈 광도곡선)")
microlensing_graph_placeholder = st.empty()


# --- 미세중력렌즈 배율 계산 함수 (간단화된 버전) ---
# u: 무차원 충격 매개변수 (렌즈-광원 사이의 최소 거리)
def calculate_microlensing_magnification(u):
    # 단일 렌즈 방정식: A = (u^2 + 2) / (u * sqrt(u^2 + 4))
    # u가 0에 가까워질수록 A는 무한대로 발산하므로, 작은 epsilon을 더합니다.
    u_safe = np.maximum(u, 1e-3) # 0으로 나누는 것 방지 및 극단적 값 제한
    magnification = (u_safe**2 + 2) / (u_safe * np.sqrt(u_safe**2 + 4))
    return magnification

# --- 시뮬레이션 로직 함수 ---
def run_simulation(system_scale_km, planet_lens_mass_kg, impact_parameter_scaled, animation_speed):
    num_frames = 600 # 프레임 수
    time_points = np.linspace(-3, 3, num_frames) # 렌즈 현상 전후를 포함하는 시간

    # 시뮬레이션 스케일
    sim_range = system_scale_km * 1e6 # 백만 km 단위를 km로
    scale_unit = sim_range / 10 # 시뮬레이션 화면 단위를 대략적인 스케일에 맞춤

    # 광원(배경 항성) 위치
    source_x, source_y = 0, 0 # 시뮬레이션 중심에 고정

    # 렌즈(외계 행성) 경로
    # 시간(time_points)에 따라 X축으로 이동 (항성 앞을 지나감)
    # 충격 매개변수를 Y축 초기 위치로 설정
    lens_x_path = time_points * (scale_unit / 2) # X축 이동 속도 조절
    lens_y_path = impact_parameter_scaled * (scale_unit / 5) # Y축 충격 매개변수 (최대 시뮬레이션 범위의 1/5)

    # 블랙홀은 배경으로만 존재 (움직이지 않음)
    bh_x, bh_y = -scale_unit * 0.8, -scale_unit * 0.8 # 시뮬레이션 가장자리 구석에 배치
    bh_size = np.cbrt(planet_lens_mass_kg / 1e25) * 20 # 행성 질량에 비례하여 크기 조정 (너무 작지 않게)
    
    # 별의 고정된 위치를 미리 생성
    num_stars = 2000
    star_x_bg = np.random.uniform(-scale_unit * 1.5, scale_unit * 1.5, num_stars)
    star_y_bg = np.random.uniform(-scale_unit * 1.5, scale_unit * 1.5, num_stars)
    star_sizes = np.random.uniform(0.5, 3.5, num_stars)
    star_opacities = np.random.uniform(0.4, 1.0, num_stars)

    magnification_data_list = [] # 배율 데이터 저장

    for i in range(num_frames):
        current_lens_x = lens_x_path[i]
        current_lens_y = lens_y_path # Y축은 고정 (일직선 통과)

        # 미세중력렌즈 배율 계산을 위한 'u' (무차원 충격 매개변수)
        # 렌즈와 광원 사이의 현재 거리 (시뮬레이션 스케일)
        # 광원은 (0,0)에 있고 렌즈는 (current_lens_x, current_lens_y)에 있음
        current_distance_between_lens_source = np.sqrt(current_lens_x**2 + current_lens_y**2)
        
        # 'u_0' (최소 접근 거리)를 impact_parameter_scaled에 비례하게 설정
        # 0.01은 광원의 반지름, 1은 렌즈의 아인슈타인 반경 등 스케일링 필요
        # 여기서는 시뮬레이션 스케일에 맞춰 직관적으로 u값을 생성
        # 예: 렌즈가 광원 중심을 지날 때 u=0, 멀리 떨어질수록 u 증가
        # 스케일링을 위해 시스템 스케일을 사용
        u_0 = impact_parameter_scaled * 2.0 # 0.0에서 2.0 사이의 u_0
        
        # 현재 시간 스텝에서의 u 값 (렌즈의 상대 위치)
        u_current = np.sqrt((current_lens_x / (scale_unit * 0.1))**2 + u_0**2) # X축 거리에 따라 u 변화
        
        magnification = calculate_microlensing_magnification(u_current)
        magnification_data_list.append(magnification)
        
        fig_sim = go.Figure()

        # 흰색 배경 설정
        fig_sim.update_layout(
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-scale_unit, scale_unit]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-scale_unit, scale_unit]),
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=600
        )

        # 배경 별
        fig_sim.add_trace(go.Scatter(
            x=star_x_bg, y=star_y_bg,
            mode='markers',
            marker=dict(size=star_sizes, color='lightgray', opacity=star_opacities, line_width=0),
            name='Stars'
        ))

        # 배경 항성 (광원)
        fig_sim.add_trace(go.Scatter(
            x=[source_x], y=[source_y],
            mode='markers',
            marker=dict(
                size=30 + (magnification - 1) * 2, # 배율에 따라 크기 변화 (밝기 변화 시각화)
                color='gold',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle' # 배경 항성은 원형
            ),
            name='Source Star'
        ))
        
        # 렌즈 (외계 행성) - 광원 앞을 지나가는 작은 천체
        fig_sim.add_trace(go.Scatter(
            x=[current_lens_x], y=[current_lens_y],
            mode='markers',
            marker=dict(
                size=15, # 행성 크기 고정
                color='deepskyblue',
                opacity=0.8,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Exoplanet (Lens)'
        ))

        # 블랙홀 (시뮬레이션 배경의 일부로 추가)
        # 블랙홀의 아크리션 디스크 (강착원반)
        for k in range(10, 0, -1):
            disk_radius = bh_size * k * 0.4 / 10
            color_val = int(255 * (k / 10))
            fig_sim.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=bh_x - disk_radius, y0=bh_y - disk_radius,
                              x1=bh_x + disk_radius, y1=bh_y + disk_radius,
                              fillcolor=f'rgba(255, {color_val}, 0, {0.05 + k*0.05})',
                              line_width=0,
                              layer="below")

        # 보라빛 블랙홀 (중앙)
        fig_sim.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y],
            mode='markers',
            marker=dict(
                size=bh_size,
                color='purple',
                opacity=0.6,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 실시간 시뮬레이션 표시
        with simulation_placeholder:
            st.plotly_chart(fig_sim, use_container_width=True, config={'displayModeBar': False})
        time.sleep(0.01 / animation_speed) # 속도 조절

    # --- 그래프 데이터 준비 ---
    # 미세중력렌즈는 행성 궤도와 직접적인 관련이 적으므로, 이 그래프는 제거하거나 다른 데이터로 대체 가능
    # 여기서는 시간(프레임)에 따른 배율 변화만 집중합니다.

    fig_microlensing = make_microlensing_graph(time_points, np.array(magnification_data_list))

    return fig_microlensing

# 미세중력렌즈 그래프 함수 이름 변경 및 로직 수정
def make_microlensing_graph(time, magnification):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=magnification, mode='lines', name='밝기 배율', line=dict(color='blue', width=2))) # 색상 변경

    fig.update_layout(
        title="외계 행성에 의한 항성의 밝기 변화 (미세중력렌즈 광도곡선)",
        xaxis_title="시간 (상대 단위)",
        yaxis_title="밝기 배율 (A)",
        template="plotly_white",
        hovermode="x unified",
        height=350, # 높이 조절
        yaxis_range=[0.8, np.max(magnification)*1.1] # y축 범위 조정 (1 이하로 떨어질 수 있음)
    )
    return fig

# --- 시뮬레이션 실행 및 업데이트 ---
if st.button("시뮬레이션 시작"):
    with st.spinner("시뮬레이션 실행 중... (시간이 다소 소요될 수 있습니다.)"):
        fig_microlensing = run_simulation(
            system_scale_km, planet_lens_mass_kg, impact_parameter_scaled, animation_speed
        )
        
    st.success("시뮬레이션 완료!")
    
    # 미세중력렌즈 그래프만 표시
    with microlensing_graph_placeholder:
        st.plotly_chart(fig_microlensing, use_container_width=True)
