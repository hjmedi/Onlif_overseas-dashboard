import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 모든 시트 데이터 로드 및 매핑 함수
@st.cache_data
def load_all_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    
    # 시트 구성
    sheets = {
        "HQ": "HQ_실적",
        "온리프": "온리프_실적",
        "르샤인": "르샤인_실적",
        "오블리브": "오블리브(송도)_실적"
    }
    
    # 각 시트별 날짜 헤더 행 위치
    header_rows = {"HQ": 5-1, "온리프": 6-1, "르샤인": 5-1, "오블리브": 6-1}
    
    data_frames = {}
    col_maps = {}
    
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}

    for key, s_name in sheets.items():
        try:
            df = pd.read_excel(file_name, sheet_name=s_name, header=None)
            data_frames[key] = df
            
            # 날짜 열 매핑
            h_row = df.iloc[header_rows[key]]
            c_map = {}
            for m_label, m_val in months_dict.items():
                for i, cell in enumerate(h_row):
                    if str(m_val) in str(cell).replace(".0", ""):
                        c_map[m_label] = i
                        break
            col_maps[key] = c_map
        except:
            st.error(f"시트 '{s_name}' 로드 실패")
            
    return data_frames, col_maps

# 3. 데이터 추출 헬퍼 함수
def get_val(df, row, col):
    if col is None or pd.isna(col): return 0
    v = pd.to_numeric(df.iloc[row, col], errors='coerce')
    return (v if pd.notnull(v) else 0) / 1000000

# 4. 사이드바 구성
st.sidebar.header("🔍 경영 실적 필터")
selected_main_bu = st.sidebar.selectbox(
    "🏢 대상 BU 선택", 
    ["전체 연결", "법인 연결", "메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"]
)

try:
    dfs, maps = load_all_data()
    all_months = list(maps["온리프"].keys()) # 기준 월 리스트

    # 기간 선택 슬라이더
    st.sidebar.markdown("### 📈 트렌드 차트 기간 설정")
    start_m, end_m = st.sidebar.select_slider(
        "기간 선택", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed"
    )
    selected_months = all_months[all_months.index(start_m) : all_months.index(end_m) + 1]

    # --- 실적 계산 로직 ---
    st.title(f"🚀 {selected_main_bu} 경영 리포트")
    st.info(f"📅 조회 기간: {start_m} ~ {end_m} (단위: 백만 원)")

    # 1. '전체 연결' 처리
    if selected_main_bu == "전체 연결":
        # 매출: 병원 3개 합계 / 영업이익: 3개 BU 합계 + HQ
        res_sales = [get_val(dfs["온리프"], 77-1, maps["온리프"][m]) + 
                     get_val(dfs["르샤인"], 85-1, maps["르샤인"][m]) + 
                     get_val(dfs["오블리브"], 83-1, maps["오블리브"][m]) for m in selected_months]
        
        res_profit = [get_val(dfs["온리프"], 52-1, maps["온리프"][m]) + 
                      get_val(dfs["르샤인"], 60-1, maps["르샤인"][m]) + 
                      get_val(dfs["오블리브"], 58-1, maps["오블리브"][m]) + 
                      get_val(dfs["HQ"], 51-1, maps["HQ"][m]) for m in selected_months]
        
        display_mapping = {"🌐 그룹 전체 연결 실적 (병원 매출 합계 + BU 전체 영업이익 합계)": {"sales": res_sales, "profit": res_profit}}

    # 2. '법인 연결' 처리
    elif selected_main_bu == "법인 연결":
        # 매출: HQ + 앤파트너스 3개 합계 / 영업이익: 앤파트너스 3개 합계 + HQ
        res_sales = [get_val(dfs["HQ"], 14-1, maps["HQ"][m]) + 
                     get_val(dfs["온리프"], 121-1, maps["온리프"][m]) + 
                     get_val(dfs["르샤인"], 132-1, maps["르샤인"][m]) + 
                     get_val(dfs["오블리브"], 130-1, maps["오블리브"][m]) for m in selected_months]
        
        res_profit = [get_val(dfs["온리프"], 155-1, maps["온리프"][m]) + 
                      get_val(dfs["르샤인"], 163-1, maps["르샤인"][m]) + 
                      get_val(dfs["오블리브"], 163-1, maps["오블리브"][m]) + 
                      get_val(dfs["HQ"], 51-1, maps["HQ"][m]) for m in selected_months]
        
        display_mapping = {"🏢 법인 연결 실적 (본사 + 앤파트너스 합산)": {"sales": res_sales, "profit": res_profit}}

    # 3. 개별 BU 처리 (기존 로직 수직 나열)
    else:
        # 각 BU별 행 번호 매핑
        key_map = {"메디빌더": "HQ", "온리프 BU": "온리프", "르샤인 BU": "르샤인", "오블리브 BU": "오블리브"}
        k = key_map[selected_main_bu]
        
        if k == "HQ":
            row_map = {"📊 메디빌더 본사(HQ) 전체 실적": {"매출": 14-1, "영익": 51-1}}
        elif k == "온리프":
            row_map = {"📊 온리프 BU 합계": {"매출": 25-1, "영익": 52-1}, "🏥 온리프 성형외과": {"매출": 77-1, "영익": 116-1}, "🤝 온리프앤파트너스": {"매출": 121-1, "영익": 155-1}}
        elif k == "르샤인":
            row_map = {"📊 르샤인 BU 합계": {"매출": 36-1, "영익": 60-1}, "🏥 르샤인 클리닉": {"매출": 85-1, "영익": 127-1}, "🤝 르샤인앤파트너스": {"매출": 132-1, "영익": 163-1}}
        else:
            row_map = {"📊 오블리브 BU 합계": {"매출": 34-1, "영익": 58-1}, "🏥 오블리브 의원": {"매출": 83-1, "영익": 125-1}, "🤝 오블리브앤파트너스": {"매출": 130-1, "영익": 163-1}}
        
        display_mapping = {}
        for title, rows in row_map.items():
            display_mapping[title] = {
                "sales": [get_val(dfs[k], rows["매출"], maps[k][m]) for m in selected_months],
                "profit": [get_val(dfs[k], rows.get("영익") or rows.get("영업이익"), maps[k][m]) for m in selected_months]
            }

    # --- 그래프 시각화 공통 ---
    color_map = {"전체 연결": "#E91E63", "법인 연결": "#9C27B0", "메디빌더": "#333333", "온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
    theme_color = color_map.get(selected_main_bu, "#31333F")

    for title, data in display_mapping.items():
        st.markdown(f"## {title}")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=selected_months, y=data["profit"], name="영업이익", marker_color=theme_color, opacity=0.6, text=[f"{v:,.0f}" for v in data["profit"]], textposition="outside"))
        fig.add_trace(go.Scatter(x=selected_months, y=data["sales"], name="매출", mode="lines+markers+text", line=dict(color="#FF4B4B", width=3), text=[f"{v:,.0f}" for v in data["sales"]], textposition="top center"))
        fig.update_layout(height=500, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis=dict(title="금액 (백만 원)", tickformat=",d"), xaxis=dict(type='category'), hovermode="x unified")
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig, use_container_width=True)
        st.divider()

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
