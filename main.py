import streamlit as st
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import imageio
import io
import time

# --- 물리 상수 ---
G = 6.674e-11  # 중력 상수 (m^3 kg^-1 s^-2)
c = 3e8      # 광속 (m/s)
KM_TO_M = 1000 # km를 m로 변환
AU_TO_M = 149_597_870_700 # 1 AU in meters
LY_TO_M = 9.461e15 # 1광년 = 9.461e15 미터

# --- 페이지 설정 ---
st.set_page_config(
    page_title="복합 중력 렌즈 시뮬레이션",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일링 (전체 인터페이스는 흰색 유지, 시뮬레이션 캔버스만 검정) ---
st.markdown(
    """
    <style>
    .reportview-container {
        background: white; /* 전체 배경을 흰색으로 설정 (사이드바, 제목 등) */
    }
    .main .block-container {
        padding-top: 2rem;
        padding-right: 2rem;
        padding-left: 2rem;
        padding-bottom: 2rem;
    }
    .stPlotlyChart {
        background: black; /* 시뮬레이션 영역만 검정색 */
        border-radius: 10px; /* 모서리를 둥글게 */
        box-shadow: 0 4px 8px rgba(0,0,0,0.3); /* 검정 배경에 맞게 그림자 조정 */
    }
    /* Matplotlib 그래프 배경도 어둡게 설정 (Streamlit의 자체 CSS에 의해 적용) */
    .stApp {
        background-color: white; /* 전체 앱 배경 */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌟 복합 중력 렌즈 시뮬레이션")
st.write("블랙홀, 항성, 행성 시스템에서 발생하는 중력 렌즈 현상과 관측되는 빛의 밝기 변화를 시뮬레이션합니다.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 변수 설정")

# 1. 블랙홀 질량
bh_mass_exponent = st.sidebar.slider(
    "블랙홀 질량 지수 (10^X kg)",
    min_value=30.0,
    max_value=40.0,
    value=36.0, # 10^6 태양 질량 (초거대 블랙홀)
    step=0.1,
    help="주 렌즈 역할을 하는 블랙홀의 질량입니다. 질량이 클수록 렌즈 효과가 강해집니다."
)
bh_mass_kg = 10**bh_mass_exponent
st.sidebar.write(f"설정된 블랙홀 질량: {bh_mass_kg:.2e} kg")

# 2. 항성 질량
star_mass_exponent = st.sidebar.slider(
    "항성 질량 지수 (10^X kg)",
    min_value=28.0, # 태양 질량 (10^30 kg) 근처
    max_value=31.0,
    value=30.0,
    step=0.1,
    help="블랙홀 주위를 공전하는 항성의 질량입니다. 미세 중력 렌즈 효과에 기여합니다."
)
star_mass_kg = 10**star_mass_exponent
st.sidebar.write(f"설정된 항성 질량: {star_mass_kg:.2e} kg")

# 3. 행성 질량
planet_mass_exponent = st.sidebar.slider(
    "행성 질량 지수 (10^X kg)",
    min_value=23.0, # 지구 질량 (10^24 kg) 근처
    max_value=27.0, # 목성 질량 (10^27 kg) 근처
    value=25.0,
    step=0.1,
    help="항성 주위를 공전하는 행성의 질량입니다. 그래프의 미세한 굴곡을 만듭니다."
)
planet_mass_kg = 10**planet_mass_exponent
st.sidebar.write(f"설정된 행성 질량: {planet_mass_kg:.2e} kg")

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
st.sidebar.write(f"설정된 블랙홀-항성 거리: {bh_star_distance_au:.0f} AU ({bh_star_distance_m/AU_TO_M:.2e} AU)")


# 5. 행성-항성 거리 (AU)
planet_star_distance_au = st.sidebar.slider(
    "행성-항성 거리 (AU)",
    min_value=0.1,
    max_value=5.0,
    value=1.0,
    step=0.1,
    help="행성이 항성을 공전하는 평균 거리입니다. (단위: AU)"
)
planet_star_distance_m = planet_star_distance_au * AU_TO_M
st.sidebar.write(f"설정된 행성-항성 거리: {planet_star_distance_au:.1f} AU ({planet_star_distance_m/AU_TO_M:.2e} AU)")


# 6. 시뮬레이션 속도
animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by AI Assistant")

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
                   bh_star_distance_m, planet_star_distance_m, animation_speed):
    
    num_frames = 600 # 프레임 수 (애니메이션 길이)
    time_points = np.arange(num_frames) # 시간축 (프레임 단위)

    # --- 거리 설정 (개념적, 광년 단위는 시뮬레이션 스케일링에 사용) ---
    # 실제 우주적 거리는 매우 크므로, 시뮬레이션 공간에 맞게 스케일링합니다.
    # D_L: 관측자-렌즈(블랙홀) 거리
    # D_S: 관측자-광원 거리
    # D_LS: 렌즈(블랙홀)-광원 거리
    
    # 여기서는 D_L, D_LS를 고정된 값으로 가정하고, 블랙홀의 아인슈타인 반경을 계산합니다.
    # 시뮬레이션의 스케일을 위해 D_L과 D_LS를 적절히 설정합니다.
    D_L_concept_ly = 5000 # 관측자-블랙홀 거리 (광년)
    D_LS_concept_ly = 5000 # 블랙홀-광원 거리 (광년)
    D_S_concept_ly = D_L_concept_ly + D_LS_concept_ly # 관측자-광원 거리 (광년)

    # 미터 단위로 변환
    D_L_m = D_L_concept_ly * LY_TO_M
    D_LS_m = D_LS_concept_ly * LY_TO_M
    D_S_m = D_S_concept_ly * LY_TO_M

    # --- 아인슈타인 반경 계산 (각 질량체별) ---
    # R_E = sqrt(4GM/c^2 * D_L * D_LS / D_S)
    
    # 블랙홀의 아인슈타인 반경 (m)
    einstein_radius_bh_m = np.sqrt((4 * G * bh_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))
    
    # 항성의 아인슈타인 반경 (m) - 항성이 미세 렌즈 역할을 할 때
    # 항성 자체의 아인슈타인 반경은 매우 작으므로, D_L, D_LS, D_S를 항성 기준으로 다시 설정해야 하지만
    # 여기서는 간단화를 위해 블랙홀 시스템의 D_L, D_LS, D_S를 공유하며 질량만 다르게 적용
    einstein_radius_star_m = np.sqrt((4 * G * star_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))

    # 행성의 아인슈타인 반경 (m) - 행성이 미세 렌즈 역할을 할 때
    einstein_radius_planet_m = np.sqrt((4 * G * planet_mass_kg / c**2) * (D_L_m * D_LS_m / D_S_m))

    # --- 시뮬레이션 공간 스케일 설정 ---
    # 시뮬레이션 화면의 x, y 범위를 블랙홀의 아인슈타인 반경을 기준으로 설정
    # 예를 들어, 화면의 절반이 블랙홀 아인슈타인 반경의 2배가 되도록
    sim_scale_factor = 2.5 # 아인슈타인 반경의 몇 배를 화면 절반으로 할지
    sim_unit_m_per_plotly_unit = einstein_radius_bh_m / sim_scale_factor # Plotly 1단위가 몇 미터인지
    sim_range_plotly_units = sim_scale_factor * 2 # Plotly 화면 범위 (-sim_scale_factor ~ +sim_scale_factor)

    # 블랙홀 위치 (중심)
    bh_x, bh_y = 0, 0
    bh_size_visual = 20 # 시각적인 블랙홀 크기 (고정)

    # 광원 위치 (블랙홀 뒤에 고정된 먼 별, 시뮬레이션의 가상 Y축 아래)
    source_x, source_y = 0, -sim_range_plotly_units * 0.8 # 시뮬레이션 화면 아래쪽에 고정

    frames_for_gif = []
    magnification_data_list = []

    # --- 궤도 매개변수 ---
    # 항성의 블랙홀 주위 공전 주기 (시뮬레이션 프레임 수에 비례하여 설정)
    # 시뮬레이션 동안 항성이 몇 바퀴 돌지 결정
    star_orbit_cycles = 1.0 # 시뮬레이션 동안 항성이 1바퀴 공전
    star_angular_speed = 2 * np.pi * star_orbit_cycles / num_frames

    # 행성의 항성 주위 공전 주기 (항성보다 훨씬 빠르게 설정하여 굴곡 생성)
    planet_orbit_cycles = 10.0 # 시뮬레이션 동안 행성이 10바퀴 공전
    planet_angular_speed = 2 * np.pi * planet_orbit_cycles / num_frames

    # 관측자의 시선이 렌즈 시스템을 가로지르는 가상의 궤적 (배율 변화 유도)
    # 여기서는 광원이 X축으로 움직이는 것처럼 모델링하여 배율 변화를 유도
    # (실제로는 관측자가 움직이거나 렌즈 시스템이 움직이는 효과)
    source_apparent_x_trajectory = np.linspace(-sim_range_plotly_units * 0.5, sim_range_plotly_units * 0.5, num_frames)

    for i in range(num_frames):
        # --- 궤도 계산 ---
        # 항성의 블랙홀 주위 공전
        star_orbit_angle = star_angular_speed * i
        current_star_x_bh_centered = (bh_star_distance_m / sim_unit_m_per_plotly_unit) * np.cos(star_orbit_angle)
        current_star_y_bh_centered = (bh_star_distance_m / sim_unit_m_per_plotly_unit) * np.sin(star_orbit_angle)
        
        # 행성의 항성 주위 공전
        planet_orbit_angle = planet_angular_speed * i
        current_planet_x_star_centered = (planet_star_distance_m / sim_unit_m_per_plotly_unit) * np.cos(planet_orbit_angle)
        current_planet_y_star_centered = (planet_star_distance_m / sim_unit_m_per_plotly_unit) * np.sin(planet_orbit_angle)

        # 행성의 절대 위치 (블랙홀 중심 기준)
        current_planet_x_bh_centered = current_star_x_bh_centered + current_planet_x_star_centered
        current_planet_y_bh_centered = current_star_y_bh_centered + current_planet_y_star_centered

        # --- 중력 렌즈 배율 계산 ---
        # 광원의 현재 (가상) X 위치 (관측자 시선에 대한 상대적 위치)
        current_apparent_source_x = source_apparent_x_trajectory[i]

        # 1. 블랙홀에 의한 기본 중력 렌즈 배율
        # 광원(current_apparent_source_x, source_y)이 블랙홀(0,0)에 대해 얼마나 가까운가
        # 여기서 u는 Plotly 단위 스케일에서의 아인슈타인 반경 대비 상대적 거리
        u_bh = np.sqrt(current_apparent_source_x**2 + source_y**2) / (einstein_radius_bh_m / sim_unit_m_per_plotly_unit)
        magnification_bh = calculate_magnification_point_lens(u_bh)

        # 2. 항성에 의한 미세 중력 렌즈 배율 섭동
        # 항성 (current_star_x_bh_centered, current_star_y_bh_centered)이 광원 시선에 얼마나 가까운가
        # (광원 시선은 대략 X=current_apparent_source_x, Y=0 라인으로 가정)
        # 항성과 광원 시선 사이의 최소 거리 (X축으로만 고려)
        dist_star_to_LOS = np.abs(current_star_x_bh_centered - current_apparent_source_x)
        u_star_microlens = dist_star_to_LOS / (einstein_radius_star_m / sim_unit_m_per_plotly_unit)
        perturbation_star = calculate_magnification_point_lens(u_star_microlens) # 항성 자체의 배율

        # 3. 행성에 의한 미세 중력 렌즈 배율 섭동 (굴곡의 주 원인)
        # 행성 (current_planet_x_bh_centered, current_planet_y_bh_centered)이 광원 시선에 얼마나 가까운가
        dist_planet_to_LOS = np.abs(current_planet_x_bh_centered - current_apparent_source_x)
        u_planet_microlens = dist_planet_to_LOS / (einstein_radius_planet_m / sim_unit_m_per_plotly_unit)
        perturbation_planet = calculate_magnification_point_lens(u_planet_microlens) # 행성 자체의 배율
        
        # 최종 배율 = 블랙홀 배율 * 항성 섭동 * 행성 섭동
        # 각 렌즈 효과가 독립적으로 작용하여 밝기를 증폭시킨다고 가정 (간단화된 모델)
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
            width=800 # 고정 너비로 설정하여 GIF 품질 유지
        )

        # 블랙홀의 아크리션 디스크 (강착원반) - 주황색 그라데이션
        for k in range(10, 0, -1):
            disk_radius = bh_size_visual * k * 0.4 / 10 * (sim_range_plotly_units / bh_size_visual) * 0.1 # 시뮬레이션 스케일에 맞춤
            color_val = int(255 * (k / 10))
            fig_sim.add_shape(type="circle",
                              xref="x", yref="y",
                              x0=bh_x - disk_radius, y0=bh_y - disk_radius,
                              x1=bh_x + disk_radius, y1=bh_y + disk_radius,
                              fillcolor=f'rgba(255, {color_val}, 0, {0.05 + k*0.05})', # 주황색 계열
                              line_width=0,
                              layer="below")

        # 블랙홀 (검은색)
        fig_sim.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y],
            mode='markers',
            marker=dict(
                size=bh_size_visual,
                color='black', # 블랙홀은 검은색
                opacity=1.0,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 광원 (밝기 및 크기 변화)
        source_visual_size = 20 + (final_magnification - 1) * 0.5 # 배율에 따라 크기 변화
        fig_sim.add_trace(go.Scatter(
            x=[current_apparent_source_x], y=[source_y],
            mode='markers',
            marker=dict(
                size=source_visual_size,
                color='gold', # 광원은 금색
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
                size=15, # 항성 크기
                color='yellow', # 항성 색상
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
                size=8, # 행성 크기
                color='orange', # 행성 색상
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Exoplanet'
        ))

        # 개념적인 빛 경로 (광원에서 블랙홀을 거쳐 관측자로)
        # 광원에서 블랙홀 주변으로 휘어지는 곡선
        num_light_paths = 5
        light_path_color = 'white'
        for path_idx in range(num_light_paths):
            # 광원(source_x, source_y)에서 시작
            # 블랙홀 주변을 휘어져서 관측자 시점 (current_apparent_source_x, 0)으로 가는 경로
            # 간단화를 위해 블랙홀 중심을 향해 가다가 휘어지는 곡선으로 표현
            start_x = current_apparent_source_x + (path_idx - (num_light_paths-1)/2) * 0.1 # 광원 근처에서 시작점 분산
            start_y = source_y

            # 블랙홀 근처의 굴절점
            bend_x = bh_x + (start_x - bh_x) * 0.5 # 블랙홀을 향해
            bend_y = bh_y + (start_y - bh_y) * 0.5 # 블랙홀을 향해

            # 관측자 시점으로 향하는 끝점
            end_x = current_apparent_source_x + (path_idx - (num_light_paths-1)/2) * 0.1 # 관측자 시점으로 수렴
            end_y = sim_range_plotly_units * 0.8 # 화면 위쪽으로

            # 베지어 곡선처럼 부드러운 경로를 위해 중간점 추가
            mid_x1 = start_x + (bend_x - start_x) * 0.5
            mid_y1 = start_y + (bend_y - start_y) * 0.5

            mid_x2 = bend_x + (end_x - bend_x) * 0.5
            mid_y2 = bend_y + (end_y - bend_y) * 0.5

            # 빛이 휘어지는 효과를 더 강조하기 위해 블랙홀 근처에서 더 강하게 휘도록 조정
            # 블랙홀에 가까울수록 더 많이 휘도록
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

        # Plotly Figure를 이미지로 변환하여 GIF 프레임으로 사용
        img_bytes = fig_sim.to_image(format="png", width=800, height=600, scale=1)
        frames_for_gif.append(imageio.v2.imread(io.BytesIO(img_bytes)))

        # 실시간 시뮬레이션 표시 (GIF 생성 중 미리보기)
        with simulation_placeholder:
            st.plotly_chart(fig_sim, use_container_width=True, config={'displayModeBar': False})
        time.sleep(0.01 / animation_speed)

    # Matplotlib 그래프 생성
    matplotlib_fig = make_magnification_graph(time_points, np.array(magnification_data_list))

    return frames_for_gif, matplotlib_fig

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
    ax.set_ylim(0.8, np.max(magnification)*1.1 if np.max(magnification) > 1.0 else 2.0) # y축 범위 조정

    plt.tight_layout() # 레이아웃 자동 조정
    return fig

# --- 시뮬레이션 실행 및 업데이트 ---
if st.button("시뮬레이션 시작 및 GIF 생성"):
    with st.spinner("시뮬레이션 실행 중... (GIF 생성에 시간이 걸릴 수 있습니다.)"):
        frames_for_gif, matplotlib_fig = run_simulation(
            bh_mass_kg, star_mass_kg, planet_mass_kg, 
            bh_star_distance_m, planet_star_distance_m, animation_speed
        )

        # GIF 생성 및 저장
        gif_path = "gravity_lens_simulation.gif"
        imageio.mimsave(gif_path, frames_for_gif, fps=20 * animation_speed) # fps는 초당 프레임 수
        
    st.success("시뮬레이션 완료 및 GIF 생성!")
    
    # 생성된 GIF 표시
    gif_placeholder.image(gif_path, caption="중력 렌즈 시뮬레이션 GIF", use_column_width=True)

    # 중력 렌즈 배율 변화 그래프 표시 (Matplotlib)
    with magnification_graph_placeholder:
        st.pyplot(matplotlib_fig) # Matplotlib Figure를 Streamlit에 표시
    
    # Matplotlib Figure 닫기 (메모리 절약)
    plt.close(matplotlib_fig)
