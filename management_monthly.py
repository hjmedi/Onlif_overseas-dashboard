import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_bu_data(selected_bu):
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    
    # BU별 시트명 및 날짜 헤더 위치 설정 (사용자 제공 정보 반영)
    bu_configs = {
        "메디빌더": {"sheet": "HQ_실적", "header_row": 5-1},
        "온리프 BU": {"sheet": "온리프_실적", "header_row": 6-1},
        "르샤인 BU": {"sheet": "르샤인_실적", "header_row": 5-1},
        "오블리브 BU": {"sheet": "오블리브(송도)_실적", "header_row": 6-1}
    }
    
    config = bu_configs[selected_bu]
    
    try:
        df = pd.read_excel(file_name, sheet_name=config["sheet"], header=None)
    except Exception as e:
        st.error(f"시트 '{config['sheet']}'를 찾을 수 없습니다. 파일 내 시트 이름을 확인해 주세요.")
        return None, {}
    
    header_data = df.iloc[config["header_row"]]
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}
    
    col_map = {}
    for m_label, m_val in months_dict.items():
        for i, cell in enumerate(header_data):
            if str(m_val) in str(cell).replace(".0", ""):
                col_map[m_label] = i
                break
    return df, col_map

# 3. 사이드바 필터
st.sidebar.header("🔍 경영 실적 필터")
selected_main_bu = st.sidebar.selectbox("🏢 대상 BU 선택", ["메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    df, col_map = load_bu_data(selected_main_bu)
    
    if df is not None:
        all_months = list(col_map.keys())

        # --- 기간 선택 슬라이더 ---
        st.sidebar.markdown("### 📈 트렌드 차트 기간 설정")
        if all_months:
            start_m, end_m = st.sidebar.select_slider(
                "기간 선택", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed"
            )
            start_idx = all_months.index(start_m)
            end_idx = all_months.index(end_m)
            selected_months = all_months[start_idx : end_idx + 1]
        else:
            selected_months = []

        # --- 행 번호 매핑 (메디빌더 HQ 정보 반영) ---
        if selected_main_bu == "메디빌더":
            row_mapping = {
                "📊 메디빌더 본사(HQ) 전체 실적": {"매출": 14-1, "영업이익": 51-1}
            }
        elif selected_main_bu == "온리프 BU":
            row_mapping = {
                "📊 온리프 BU 전체 (합계)": {"매출": 25-1, "영업이익": 52-1},
                "🏥 온리프 성형외과 (의원)": {"매출": 77-1, "영업이익": 116-1},
                "🤝 온리프앤파트너스 (법인)": {"매출": 121-1, "영업이익": 155-1}
            }
        elif selected_main_bu == "르샤인 BU":
            row_mapping = {
                "📊 르샤인 BU 전체 (합계)": {"매출": 36-1, "영업이익": 60-1}, 
                "🏥 르샤인 클리닉 (의원)": {"매출": 85-1, "영업이익": 127-1},
                "🤝 르샤인앤파트너스 (법인)": {"매출": 132-1, "영업이익": 163-1}
            }
        else: # 오블리브 BU
            row_mapping = {
                "📊 오블리브 BU 전체 (합계)": {"매출": 34-1, "영업이익": 58-1},
                "🏥 오블리브 의원 (의원)": {"매출": 83-1, "영업이익": 125-1},
                "🤝 오블리브앤파트너스 (법인)": {"매출": 130-1, "영업이익": 163-1}
            }

        # 메인 화면
        st.title(f"🚀 {selected_main_bu} 경영 리포트")
        
        if not selected_months:
            st.warning("데이터를 불러올 수 없습니다. 엑셀 구조를 확인해 주세요.")
        else:
            st.info(f"📅 조회 기간: {start_m} ~ {end_m} (단위: 백만 원)")
            
            color_map = {"메디빌더": "#333333", "온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
            theme_color = color_map.get(selected_main_bu, "#31333F")

            for section_title, rows in row_mapping.items():
                st.markdown(f"## {section_title}")
                
                sales_vals = [pd.to_numeric(df.iloc[rows["매출"], col_map[m]], errors='coerce') / 1000000 for m in selected_months]
                profit_vals = [pd.to_numeric(df.iloc[rows["영업이익"], col_map[m]], errors='coerce') / 1000000 for m in selected_months]
                
                fig = go.Figure()
                # 영업이익 막대
                fig.add_trace(go.Bar(
                    x=selected_months, y=profit_vals, name="영업이익",
                    marker_color=theme_color, opacity=0.6,
                    text=[f"{v:,.0f}" for v in profit_vals], textposition="outside"
                ))
                # 매출 꺾은선
                fig.add_trace(go.Scatter(
                    x=selected_months, y=sales_vals, name="매출",
                    mode="lines+markers+text", line=dict(color="#FF4B4B", width=3),
                    text=[f"{v:,.0f}" for v in sales_vals], textposition="top center"
                ))

                fig.update_layout(
                    height=500, margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis=dict(title="금액 (백만 원)", tickformat=",d"),
                    xaxis=dict(type='category'),
                    hovermode="x unified"
                )
                fig.add_hline(y=0, line_dash="dash", line_color="black")
                st.plotly_chart(fig, use_container_width=True)
                st.divider()

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
