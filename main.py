import streamlit as st
import numpy as np
import plotly.graph_objects as go # Plotly는 시뮬레이션 시각화에 여전히 사용
import matplotlib.pyplot as plt # Matplotlib 그래프를 위해 추가
import matplotlib.image as mpimg # Matplotlib에서 이미지 처리를 위해 (필수는 아님)
import time
import imageio # GIF 생성을 위해 추가
import io # 바이트 스트림 처리를 위해 추가

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
    /* 시뮬레이션 캔버스 배경을 검정색으로 설정 */
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

st.title("💫 복합 중력 렌즈 시뮬레이션")
st.write("블랙홀, 항성, 행성의 복합적인 중력 렌즈 효과와 빛의 밝기 변화를 시뮬레이션합니다.")

# --- 사이드바 설정 ---
st.sidebar.header("시뮬레이션 변수 설정")

# 1. 블랙홀과 항성 사이의 초기 거리 (km)
bh_star_initial_distance_km = st.sidebar.slider(
    "블랙홀-항성 초기 거리 (백만 km)",
    min_value=10,
    max_value=100,
    value=50,
    step=1,
    help="블랙홀과 항성(중앙 별) 사이의 초기 거리입니다. (단위: 백만 km)"
)
bh_star_initial_distance_scaled = bh_star_initial_distance_km * 1e6 # km로 변환

# 2. 항성 질량 (렌즈 역할에도 영향)
star_mass_exponent = st.sidebar.slider(
    "항성 질량 지수 (10^X kg)",
    min_value=28.0, # 태양 질량 (10^30 kg) 근처
    max_value=31.0,
    value=30.0,
    step=0.1,
    help="블랙홀 주위를 공전하는 항성의 질량입니다."
)
star_mass_kg = 10**star_mass_exponent
st.sidebar.write(f"설정된 항성 질량: {star_mass_kg:.2e} kg")


# 3. 행성과 항성 사이의 거리 (AU)
planet_star_distance_au = st.sidebar.slider(
    "행성-항성 거리 (AU)",
    min_value=0.1,
    max_value=2.0,
    value=1.0,
    step=0.01,
    help="행성이 항성을 공전하는 평균 거리입니다. 1 AU는 지구-태양 거리와 같습니다."
)
au_to_km = 149_597_870.7 # 1 AU in km
planet_star_distance_km = planet_star_distance_au * au_to_km
st.sidebar.write(f"설정된 행성-항성 거리: {planet_star_distance_au:.2f} AU ({planet_star_distance_km:,.0f} km)")


# 4. 행성의 질량 (렌즈 역할에도 영향)
planet_mass_exponent = st.sidebar.slider(
    "행성 질량 지수 (10^X kg)",
    min_value=23.0,
    max_value=27.0, # 목성 질량 (10^27 kg) 근처
    value=25.0,
    step=0.1,
    help="항성 주위를 공전하는 행성의 질량입니다."
)
planet_mass_kg = 10**planet_mass_exponent
st.sidebar.write(f"설정된 행성 질량: {planet_mass_kg:.2e} kg")

animation_speed = st.sidebar.slider("애니메이션 속도", 0.1, 2.0, 1.0, 0.1)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by AI Assistant")

# --- 시뮬레이션 영역 ---
st.header("시뮬레이션")
simulation_placeholder = st.empty() # 애니메이션 프레임을 표시할 곳

# --- GIF 표시를 위한 Placeholder ---
gif_placeholder = st.empty()

# --- 그래프 영역 ---
st.header("데이터 그래프")
st.subheader("관측된 빛의 밝기 변화 (복합 중력 렌즈)")
magnification_graph_placeholder = st.empty()


# --- 중력 렌즈 배율 계산 함수 ---
# 블랙홀의 중력 렌즈 효과 (기본)
def calculate_bh_magnification(impact_param, einstein_radius):
    # u = impact_param / einstein_radius
    # A = (u^2 + 2) / (u * sqrt(u^2 + 4))
    u = impact_param / einstein_radius
    if u < 1e-6: # 중심에 매우 가까울 때 발산 방지
        return 200.0 # 최대 배율 제한
    magnification = (u**2 + 2) / (u * np.sqrt(u**2 + 4))
    return magnification

# 항성/행성에 의한 미세중력렌즈 섭동 (간단화된 모델)
# 렌즈 천체가 광원 시선에 얼마나 가까이 지나가는지에 따라 추가적인 밝기 증폭
def calculate_microlensing_perturbation(distance_to_LOS, einstein_radius_of_lens):
    # distance_to_LOS: 렌즈 천체(항성/행성)가 광원-관측자 시선에서 얼마나 떨어져 있는지
    # einstein_radius_of_lens: 해당 렌즈 천체의 아인슈타인 반경 (질량에 비례)
    u = distance_to_LOS / einstein_radius_of_lens
    if u < 1e-3: # 매우 가까울 때
        return 1.0 + (1.0 / (u + 1e-4)) * 5.0 # 추가적인 피크 (더 강하게)
    return 1.0 + (1.0 / (u**2 + 1)) * 0.5 # 부드러운 섭동 (약하게)

# --- 시뮬레이션 로직 함수 ---
def run_simulation(bh_star_initial_distance_scaled, star_mass_kg, planet_star_distance_km, planet_mass_kg, animation_speed):
    num_frames = 800 # 프레임 수 증가 (부드러운 애니메이션)
    time_points = np.arange(num_frames)
    
    # 시뮬레이션 공간 스케일 (블랙홀-항성 초기 거리를 기준으로 함)
    sim_scale_unit = bh_star_initial_distance_scaled / 5e6 # 백만 km를 시뮬레이션 단위로 변환
                                                           # (예: 5000만 km -> 10단위)

    # 블랙홀 위치 (중심)
    bh_x, bh_y = 0, 0
    
    # 블랙홀 슈바르츠실트 반지름 (개념적 크기, 실제 렌즈 효과는 아인슈타인 반경으로)
    # R_s = 2GM/c^2. 여기서는 시각적 크기를 위해 대략적인 스케일로 사용
    bh_size_visual = 20 # 고정 시각적 크기 또는 질량에 비례하게 조정
    
    # 블랙홀의 아인슈타인 반경 (중력 렌즈의 스케일)
    # R_E = sqrt(4GM/c^2 * D_LS * D_L / D_S). 여기서는 간단화를 위해 질량에만 비례
    # D_L, D_S, D_LS는 거리 요소. 여기서는 대략적으로 질량에 루트 비례하도록
    G = 6.674e-11 # 중력 상수
    c = 3e8 # 광속
    
    # 태양 질량 블랙홀의 아인슈타인 반경: 약 1 AU
    # 블랙홀 질량을 따로 설정하지 않았으므로, 항성 질량에 비례하여 스케일링
    bh_mass_estimate = star_mass_kg * 1000 # 항성보다 훨씬 무거운 블랙홀 가정
    bh_einstein_radius = np.sqrt(4 * G * bh_mass_estimate / c**2) * 1e-6 # 대략적인 아인슈타인 반경 (km) 스케일링

    # 광원 (블랙홀 뒤에 고정된 먼 별)
    source_x, source_y = 0, -sim_scale_unit * 1.0 # 블랙홀 Y축 아래에 고정 (시선 일치)

    # 항성 공전 궤도 (블랙홀 주위)
    star_orbit_radius_scaled = bh_star_initial_distance_scaled / (sim_scale_unit * 1e6 / 10) # 시뮬레이션 단위로 변환
    
    # 행성 공전 궤도 (항성 주위)
    planet_orbit_radius_scaled = planet_star_distance_km / (sim_scale_unit * 1e6 / 10) # 시뮬레이션 단위로 변환

    # 별, 행성 각각의 아인슈타인 반경 (미세중력렌즈 효과용)
    star_einstein_radius = np.sqrt(4 * G * star_mass_kg / c**2) * 1e-6 # km 스케일링
    planet_einstein_radius = np.sqrt(4 * G * planet_mass_kg / c**2) * 1e-6 # km 스케일링
    
    # 배경 별
    num_stars = 2000
    star_x_bg = np.random.uniform(-sim_scale_unit * 1.5, sim_scale_unit * 1.5, num_stars)
    star_y_bg = np.random.uniform(-sim_scale_unit * 1.5, sim_scale_unit * 1.5, num_stars)
    star_sizes = np.random.uniform(0.5, 3.5, num_stars)
    star_opacities = np.random.uniform(0.4, 1.0, num_stars)

    frames_for_gif = []
    magnification_data_list = []

    for i in range(num_frames):
        # 항성의 블랙홀 주위 공전
        star_orbit_angle = 2 * np.pi * (i / num_frames) * 1.5 # 1.5바퀴 공전
        current_star_x = star_orbit_radius_scaled * np.cos(star_orbit_angle)
        current_star_y = star_orbit_radius_scaled * np.sin(star_orbit_angle)

        # 행성의 항성 주위 공전
        planet_orbit_angle = 2 * np.pi * (i / num_frames) * 5 # 행성은 더 빠르게 공전
        current_planet_x = current_star_x + planet_orbit_radius_scaled * np.cos(planet_orbit_angle)
        current_planet_y = current_star_y + planet_orbit_radius_scaled * np.sin(planet_orbit_angle)

        # 1. 블랙홀에 의한 기본 중력 렌즈 배율 계산
        # 블랙홀-광원 시선에 대한 항성의 상대적 X축 위치
        star_impact_on_LOS = current_star_x 
        
        # 여기서 bh_einstein_radius는 실제 거리에 비례하도록 스케일링 되어야 합니다.
        # 현재 sim_scale_unit으로 나눠서 시뮬레이션 공간의 스케일에 맞춤
        u_bh = (np.abs(star_impact_on_LOS) + 1e-4) / (bh_einstein_radius / sim_scale_unit) 
        magnification_bh = calculate_bh_magnification(u_bh, 1.0) 
        
        # 2. 항성에 의한 미세중력렌즈 섭동 (추가 효과)
        dist_star_to_source_LOS = np.sqrt(current_star_x**2 + current_star_y**2)
        perturbation_star = calculate_microlensing_perturbation(dist_star_to_source_LOS, star_einstein_radius / sim_scale_unit)

        # 3. 행성에 의한 미세중력렌즈 섭동 (추가 효과)
        dist_planet_to_source_LOS = np.sqrt(current_planet_x**2 + current_planet_y**2)
        perturbation_planet = calculate_microlensing_perturbation(dist_planet_to_source_LOS, planet_einstein_radius / sim_scale_unit)
        
        # 최종 배율 = 블랙홀 배율 * 항성 섭동 * 행성 섭동 (곱하는 방식으로 복합 효과)
        final_magnification = magnification_bh * perturbation_star * perturbation_planet
        final_magnification = min(final_magnification, 200.0) # 최대 배율 제한
        magnification_data_list.append(final_magnification)


        # Plotly Figure 생성 (시뮬레이션 시각화)
        fig_sim = go.Figure()

        # 검은색 배경 설정
        fig_sim.update_layout(
            paper_bgcolor='black',
            plot_bgcolor='black',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-sim_scale_unit, sim_scale_unit]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-sim_scale_unit, sim_scale_unit]),
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=600
        )

        # 배경 별 (흰색 점)
        fig_sim.add_trace(go.Scatter(
            x=star_x_bg, y=star_y_bg,
            mode='markers',
            marker=dict(size=star_sizes, color='white', opacity=star_opacities, line_width=0),
            name='Stars'
        ))

        # 블랙홀의 아크리션 디스크 (강착원반)
        for k in range(10, 0, -1):
            disk_radius = bh_size_visual * k * 0.4 / 10
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
                size=bh_size_visual,
                color='purple',
                opacity=0.6,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Black Hole'
        ))

        # 광원 (블랙홀 뒤에 고정된 먼 별) - 밝기 변화를 시각적으로 보여줌
        fig_sim.add_trace(go.Scatter(
            x=[source_x], y=[source_y],
            mode='markers',
            marker=dict(
                size=30 + (final_magnification - 1) * 2, # 배율에 따라 크기 변화
                color='gold',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Distant Source'
        ))
        
        # 항성 (블랙홀 주위 공전)
        fig_sim.add_trace(go.Scatter(
            x=[current_star_x], y=[current_star_y],
            mode='markers',
            marker=dict(
                size=20, # 항성 크기
                color='red', # 항성 색상
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Star'
        ))

        # 행성 (항성 주위 공전)
        fig_sim.add_trace(go.Scatter(
            x=[current_planet_x], y=[current_planet_y],
            mode='markers',
            marker=dict(
                size=10, # 행성 크기
                color='deepskyblue',
                opacity=0.9,
                line=dict(width=0),
                symbol='circle'
            ),
            name='Exoplanet'
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
    ax.set_title("관측된 빛의 밝기 변화 (복합 중력 렌즈 효과)", color='white')
    ax.set_xlabel("시간 (프레임)", color='white')
    ax.set_ylabel("밝기 배율 (A)", color='white')
    
    # 그래프 배경 및 텍스트 색상 설정
    fig.patch.set_facecolor('black') # 그림 전체 배경
    ax.set_facecolor('black') # 플롯 영역 배경
    ax.tick_params(axis='x', colors='white') # x축 눈금 색상
    ax.tick_params(axis='y', colors='white') # y축 눈금 색상
    ax.spines['left'].set_color('white') # 왼쪽 축 테두리
    ax.spines['bottom'].set_color('white') # 아래쪽 축 테두리
    ax.spines['right'].set_color('none') # 오른쪽 축 테두리 없앰
    ax.spines['top'].set_color('none') # 위쪽 축 테두리 없앰

    ax.grid(True, linestyle='--', alpha=0.6, color='gray') # 격자 추가
    ax.set_ylim(0.8, np.max(magnification)*1.1) # y축 범위 조정

    plt.tight_layout() # 레이아웃 자동 조정
    return fig

# --- 시뮬레이션 실행 및 업데이트 ---
if st.button("시뮬레이션 시작 및 GIF 생성"):
    with st.spinner("시뮬레이션 실행 중... (GIF 생성에 시간이 걸릴 수 있습니다.)"):
        frames_for_gif, matplotlib_fig = run_simulation(
            bh_star_initial_distance_km, star_mass_kg, planet_star_distance_km, planet_mass_kg, animation_speed
        )

        # GIF 생성 및 저장
        gif_path = "complex_gravity_lens_simulation.gif"
        imageio.mimsave(gif_path, frames_for_gif, fps=20 * animation_speed) # fps는 초당 프레임 수
        
    st.success("시뮬레이션 완료 및 GIF 생성!")
    
    # 생성된 GIF 표시
    gif_placeholder.image(gif_path, caption="복합 중력 렌즈 시뮬레이션 GIF", use_column_width=True)

    # 중력 렌즈 배율 변화 그래프 표시 (Matplotlib)
    with magnification_graph_placeholder:
        st.pyplot(matplotlib_fig) # Matplotlib Figure를 Streamlit에 표시
    
    # Matplotlib Figure 닫기 (메모리 절약)
    plt.close(matplotlib_fig)
