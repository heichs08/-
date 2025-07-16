import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import time

# --- 물리 상수 ---
G = 6.674e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 3e8      # 광속 (m/s)
AU_TO_M = 149_597_870_700 # 1 AU in meters
LY_TO_M = 9.461e15 # 1광년 = 9.461e15 미터

# --- 페이지 설정 ---
st.set_page_config(
    page_title="복합 중력 렌즈 시뮬레이터",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일링 (Streamlit 기본 배경 흰색, 시뮬레이션 캔버스만 검정) ---
st.markdown(
    """
    <style>
    /* 전체 앱의 배경색을 흰색으로 유지 */
    .stApp {
        background-color: white;
    }
    /* Streamlit 컨테이너의 패딩 조정 */
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    /* Plotly 차트가 표시되는 영역의 배경을 검정색으로 설정하고 스타일링 */
    .stPlotlyChart {
        background: black;
        border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    /* Matplotlib 그래프는 기본적으로 어둡게 설정되도록 코딩되어 있음 */
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌟 복합 중력 렌즈 시뮬레이터")
st.write("블랙홀, 항성, 행성 시스템에서 발생하는 중력 렌즈 현상과 관측되는 빛의 밝기 변화를 시뮬레이션합니다.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 변수 설정")

# 1. 블랙홀 질량
bh_mass_exponent = st.sidebar.slider(
    "블랙홀 질량 지수 (10^X kg)",
    min_value=30.0,
    max_value=40.0,
    value=36.0, # 예: 10^6 태양 질량 (초거대 블랙홀)
    step=0.1,
    help="주 렌즈 역할을 하는 블랙홀의 질량입니다. 질량이 클수록 렌즈 효과가 강해집니다."
)
bh_mass_kg = 10**bh_mass_exponent
st.sidebar.write(f"현재 설정된 블랙홀 질량: {bh_mass_kg:.2e} kg")

# 2. 항성 질량
star_mass_exponent = st.sidebar.slider(
    "항성 질량 지수 (10^X kg)",
    min_value=28.0, # 예: 태양 질량 (10^30 kg) 근처
    max_value=31.0,
    value=30.0,
    step=0.1,
    help="블랙홀 주위를 공전하는 항성의 질량입니다. 미세 중력 렌즈 효과에 기여합니다."
)
star_mass_kg = 10**star_mass_exponent
st.sidebar.write(f"현재 설정된 항성 질량: {star_mass_kg:.2e} kg")

# 3. 행성 질량 (기본값을 약간 높여 굴곡이 더 잘 보이도록 조정)
planet_mass_exponent = st.sidebar.slider(
    "행성 질량 지수 (10^X kg)",
    min_value=23.0, # 예: 지구 질량 (10^24 kg) 근처
    max_value=27.0, # 예: 목성 질량 (10^27 kg) 근처
    value=26.0, # 기본값을 10^26 kg (목성 질량보다 약간 더)로 조정하여 굴곡 강화
    step=0.1,
    help="항성 주위를 공전하는 행성의 질량입니다. 밝기 그래프에 미세한 굴곡을 만듭니다."
)
planet_mass_kg = 10**planet_mass_exponent
st.sidebar.write(f"현재 설정된 행성 질량: {planet_mass_kg:.2e} kg")

# 4. 블랙홀-항성 거리 (AU)
bh_star_distance_au = st.sidebar.slider(
    "블랙홀-항성 거리 (AU)",
    min_value=100.0,
    max_value=1000.0,
    value=500.0,
    step=10.0,
    help="항성이 블랙홀을 공전하는 평균 거리입니다. (단위: AU)"
)
bh_star_distance_m = bh_star_distance_au * AU_TO_M
st.sidebar.write(f"현재 설정된 블랙홀-항성 거리: {bh_star_distance_au:.0f} AU")


# 5. 행성-항성 거리 (AU) (기본값을 약간 줄여 정렬 가능성 높임)
planet_star_distance_au = st.sidebar.slider(
    "행성-항성 거리 (AU)",
    min_value=0.1,
    max_value=5.0,
    value=0.5, # 기본값을 0.5 AU로 조정하여 행성이 더 자주 시선에 정렬되도록 함
    step=0.1,
    help="행성이 항성을 공전하는 평균 거리입니다. (단위: AU)"
)
planet_star_distance_m = planet_star_distance_au * AU_TO_M
st.sidebar.write(f"현재 설정된 행성-항성 거리: {planet_star_distance_au:.1f} AU")


# 6. 시뮬레이션 속도
animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by AI Assistant")

# --- 시뮬레이션 영역 ---
st.header("시뮬레이션 영상")
simulation_placeholder = st.empty() # 애니메이션 프레임을 표시할 곳

# --- 그래프 영역 ---
st.header("밝기 변화 그래프")
st.subheader("관측된 광원의 밝기 배율 변화")
magnification_graph_placeholder = st.empty()

# --- 중력 렌즈 배율 계산 함수 ---
# 점 질량 렌즈의 배율 공식
def calculate_magnification_point_lens(u):
    # u = 충격 매개변수 / 아인슈타인 반경 (정규화된 거리)
    # A = (u^2 + 2) / (u * sqrt(u^2 + 4))
    if u < 1e-4: # u가 0에 가까울 때 발산 방지 및 유한한 최대 배율 설정
        return 200.0 # 최대 배율 제한 (실제로는 광원의 크기 때문에 유한)
    magnification = (u**2 + 2) / (u * np.sqrt(u**2 + 4))
    return magnification

# --- 시뮬레이션 로직 함수 ---
def run_simulation(bh_mass_kg, star_mass_kg, planet_mass_kg, 
                   bh_star_distance_m, planet_star_distance_m, animation_speed,
                   simulation_placeholder, magnification_graph_placeholder): # placeholder 인자로 받기
    
    num_frames = 600 # 시뮬레이션 프레임 수 (애니메이션 길이)
    time_points = np.arange(num_frames) # 시간축 (프레임 단위)

    # --- 거리 설정 (개념적, 광년 단위는 시뮬레이션 스케일링에 사용) ---
    D_L_concept_ly = 5000 # 관측자-블랙홀 거리 (광년)
    D_LS_concept_ly = 5000 # 블랙홀-광원 거리 (광년)
    D_S_concept_ly = D_L_concept_ly + D_LS_concept_ly # 관측자-광원 거리 (광년)

    # 미터 단위로 변환
    D_L_m = D_L_concept_ly * LY_TO_M
    D_LS_m = D_LS_concept_ly * LY_TO_M
    D_S_m = D_S_concept_ly * LY_TO_M

    # --- 아인슈타인 반경 계산 (각 질량체별) ---
    einstein_radius_bh_m = np.sqrt((4 * G * bh_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))
    einstein_radius_star_m = np.sqrt((4 * G * star_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))
    einstein_radius_planet_m = np.sqrt((4 * G * planet_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))

    # --- 시뮬레이션 공간 스케일 설정 ---
    sim_scale_factor = 2.5 # 아인슈타인 반경의 몇 배를 화면 절반으로 할지
    sim_unit_m_per_plotly_unit = einstein_radius_bh_m / sim_scale_factor # Plotly 1단위가 몇 미터인지
    sim_range_plotly_units = sim_scale_factor * 2 # Plotly 화면 범위 (-sim_scale_factor ~ +sim_scale_factor)

    # 블랙홀 위치 (중심)
    bh_x, bh_y = 0, 0
    bh_size_visual = 20 # 시각적인 블랙홀 크기 (고정)

    # 광원 위치 (블랙홀 뒤에 고정된 먼 별, 시뮬레이션의 가상 Y축 아래)
    source_x, source_y = 0, -sim_range_plotly_units * 0.8 # 시뮬레이션 화면 아래쪽에 고정

    magnification_data_list = []

    # --- 궤도 매개변수 ---
    star_orbit_cycles = 1.0 # 시뮬레이션 동안 항성이 1바퀴 공전
    star_angular_speed = 2 * np.pi * star_orbit_cycles / num_frames

    planet_orbit_cycles = 10.0 # 시뮬레이션 동안 행성이 10바퀴 공전 (굴곡 생성에 유리)
    planet_angular_speed = 2 * np.pi * planet_orbit_cycles / num_frames

    # 관측자의 시선이 렌즈 시스템을 가로지르는 가상의 궤적 (배율 변화 유도)
    source_apparent_x_trajectory = np.linspace(-sim_range_plotly_units * 0.5, sim_range_plotly_units * 0.5, num_frames)

    for i in range(num_frames):
        # --- 궤도 계산 ---
        star_orbit_angle = star_angular_speed * i
        current_star_x_bh_centered = (bh_star_distance_m / sim_unit_m_per_plotly_unit) * np.cos(star_orbit_angle)
        current_star_y_bh_centered = (bh_star_distance_m / sim_unit_m_per_plotly_unit) * np.sin(star_orbit_angle)
        
        planet_orbit_angle = planet_angular_speed * i
        current_planet_x_star_centered = (planet_star_distance_m / sim_unit_m_per_plotly_unit) * np.cos(planet_orbit_angle)
        current_planet_y_star_centered = (planet_star_distance_m / sim_unit_m_per_plotly_unit) * np.sin(planet_orbit_angle)

        current_planet_x_bh_centered = current_star_x_bh_centered + current_planet_x_star_centered
        current_planet_y_bh_centered = current_star_y_bh_centered + current_planet_y_star_centered

        # --- 중력 렌즈 배율 계산 ---
        current_apparent_source_x = source_apparent_x_trajectory[i]

        # 1. 블랙홀에 의한 기본 중력 렌즈 배율
        u_bh = np.sqrt(current_apparent_source_x**2 + source_y**2) / (einstein_radius_bh_m / sim_unit_m_per_plotly_unit)
        magnification_bh = calculate_magnification_point_lens(u_bh)

        # 2. 항성에 의한 미세 중력 렌즈 배율 섭동
        dist_star_to_LOS = np.abs(current_star_x_bh_centered - current_apparent_source_x)
        u_star_microlens = dist_star_to_LOS / (einstein_radius_star_m / sim_unit_m_per_plotly_unit)
        perturbation_star = calculate_magnification_point_lens(u_star_microlens)

        # 3. 행성에 의한 미세 중력 렌즈 배율 섭동 (굴곡의 주 원인)
        dist_planet_to_LOS = np.abs(current_planet_x_bh_centered - current_apparent_source_x)
        u_planet_microlens = dist_planet_to_LOS / (einstein_radius_planet_m / sim_unit_m_per_plotly_unit)
        perturbation_planet = calculate_magnification_point_lens(u_planet_microlens)
        
        # 최종 배율 = 블랙홀 배율 * 항성 섭동 * 행성 섭동
        final_magnification = magnification_bh * perturbation_star * perturbation_planet
        final_magnification = min(final_magnification, 500.0) # 과도한 배율 제한
        magnification_data_list.append(final_magnification)

        # --- Plotly Figure 생성 (시뮬레이션 시각화) ---
        fig_sim = go.Figure()

        fig_sim.update_layout(
            paper_bgcolor='black',
            plot_bgcolor='black',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-sim_range_plotly_units, sim_range_plotly_units]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-sim_range_plotly_units, sim_range_plotly_units]),
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=600,
            width=800
        )

        # 블랙홀의 아크리션 디스크 (강착원반) - 주황색 그라데이션
        for k in range(10, 0, -1):
            disk_radius = bh_size_visual * k * 0.4 / 10 * (sim_range_plotly_units / bh_size_visual) * 0.1
            color_val = int(255 * (k / 10))
            fig_sim.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=bh_x - disk_radius, y0=bh_y - disk_radius,
                              x1=bh_x + disk_radius, y1=bh_y + disk_radius,
                              fillcolor=f'rgba(255, {color_val}, 0, {0.05 + k*0.05})',
                              line_width=0,
                              layer="below")

        # 블랙홀 (검은색)
        fig_sim.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y],
            mode='markers',
            marker=dict(
                size=bh_size_visual,
                color='black',
                opacity=1.0,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 광원 (밝기 및 크기 변화)
        source_visual_size = 20 + (final_magnification - 1) * 0.5
        fig_sim.add_trace(go.Scatter(
            x=[current_apparent_source_x], y=[source_y],
            mode='markers',
            marker=dict(
                size=source_visual_size,
                color='gold',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Distant Source'
        ))
        
        # 항성 (노란색 원)
        fig_sim.add_trace(go.Scatter(
            x=[current_star_x_bh_centered], y=[current_star_y_bh_centered],
            mode='markers',
            marker=dict(
                size=15,
                color='yellow',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Star'
        ))

        # 행성 (주황색 원)
        fig_sim.add_trace(go.Scatter(
            x=[current_planet_x_bh_centered], y=[current_planet_y_bh_centered],
            mode='markers',
            marker=dict(
                size=8,
                color='orange',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Exoplanet'
        ))

        # 개념적인 빛 경로 (광원에서 블랙홀을 거쳐 관측자로)
        num_light_paths = 5
        light_path_color = 'white'
        for path_idx in range(num_light_paths):
            start_x = current_apparent_source_x + (path_idx - (num_light_paths-1)/2) * 0.1 
            start_y = source_y

            bend_x = bh_x + (start_x - bh_x) * 0.5 
            bend_y = bh_y + (start_y - bh_y) * 0.5 

            end_x = current_apparent_source_x + (path_idx - (num_light_paths-1)/2) * 0.1 
            end_y = sim_range_plotly_units * 0.8 

            mid_x1 = start_x + (bend_x - start_x) * 0.5
            mid_y1 = start_y + (bend_y - start_y) * 0.5

            mid_x2 = bend_x + (end_x - bend_x) * 0.5
            mid_y2 = bend_y + (end_y - bend_y) * 0.5

            curve_factor = 0.5 # 휘는 정도 조절
            mid_x1 += (bh_x - mid_x1) * curve_factor
            mid_y1 += (bh_y - mid_y1) * curve_factor
            mid_x2 += (bh_x - mid_x2) * curve_factor
            mid_y2 += (bh_y - mid_y2) * curve_factor

            fig_sim.add_trace(go.Scatter(
                x=[start_x, mid_x1, bend_x, mid_x2, end_x],
                y=[start_y, mid_y1, bend_y, mid_y2, end_y],
                mode='lines',
                line=dict(color=light_path_color, width=1, dash='dot'),
                showlegend=False
            ))

        # 실시간 시뮬레이션 표시
        with simulation_placeholder:
            st.plotly_chart(fig_sim, use_container_width=True, config={'displayModeBar': False})
        
        time.sleep(0.01 / animation_speed)

    # 시뮬레이션이 끝난 후 Matplotlib 그래프를 그립니다.
    matplotlib_fig = make_magnification_graph(time_points, np.array(magnification_data_list))
    
    with magnification_graph_placeholder:
        st.pyplot(matplotlib_fig)
    
    plt.close(matplotlib_fig) # 메모리 절약

# --- Matplotlib 그래프 생성 함수 ---
def make_magnification_graph(time, magnification):
    fig, ax = plt.subplots(figsize=(10, 4)) # 그래프 크기 설정

    ax.plot(time, magnification, color='lime', linewidth=2) # 선 그래프
    ax.set_title("관측된 광원의 밝기 변화", color='white', fontsize=16)
    ax.set_xlabel("시간 (프레임)", color='white', fontsize=12)
    ax.set_ylabel("밝기 배율 (A)", color='white', fontsize=12)
    
    # 그래프 배경 및 텍스트 색상 설정
    fig.patch.set_facecolor('black') # 그림 전체 배경
    ax.set_facecolor('black') # 플롯 영역 배경
    ax.tick_params(axis='x', colors='white') # x축 눈금 색상
    ax.tick_params(axis='y', colors='white') # y축 눈금 색상
    ax.spines['left'].set_color('white') # 왼쪽 축 테두리
    ax.spines['bottom'].set_color('white') # 아래쪽 축 테두리
    ax.spines['right'].set_color('none') # 오른쪽 축 테두리 없앰
    ax.spines['top'].set_color('none') # 위쪽 축 테두리 없앰

    ax.grid(True, linestyle='--', alpha=0.3, color='gray') # 격자 추가
    
    # Y축 범위 조정: 미세한 굴곡이 잘 보이면서도 전체적인 트렌드를 볼 수 있도록
    # 배율의 최소값과 최대값에 기반하여 유동적으로 설정
    min_mag = np.min(magnification)
    max_mag = np.max(magnification)
    
    # 기본적으로 0.8부터 시작하거나, 최소 배율보다 약간 낮게 시작
    lower_bound = max(0.8, min_mag * 0.9) 
    # 최대 배율보다 약간 높게 설정
    upper_bound = max_mag * 1.1 if max_mag > 1.0 else 2.0 
    
    ax.set_ylim(lower_bound, upper_bound)

    plt.tight_layout() # 레이아웃 자동 조정
    return fig

# --- 시뮬레이션 실행 버튼 ---
if st.button("시뮬레이션 시작"):
    with st.spinner("시뮬레이션 실행 중..."):
        # run_simulation 함수에 placeholder를 직접 전달
        run_simulation(
            bh_mass_kg, star_mass_kg, planet_mass_kg, 
            bh_star_distance_m, planet_star_distance_m, animation_speed,
            simulation_placeholder, magnification_graph_placeholder # placeholder 전달
        )
        
    st.success("시뮬레이션 완료! 아래 그래프를 확인해주세요.")
