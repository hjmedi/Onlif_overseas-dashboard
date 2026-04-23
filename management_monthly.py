import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_full_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    # 헤더 행(index 3)에서 월 정보 추출
    header_row = df.iloc[3]
    months_dict = {
        "25.01": 2501, "25.02": 2502, "25.03": 2503, "25.04": 2504, "25.05": 2505, "25.06": 2506, 
        "25.07": 2507, "25.08": 2508, "25.09": 2509, "25.10": 2510, "25.11": 2511, "25.12": 2512, 
        "26.01": 2601, "26.02": 2602
    }
    
    # 월별 열 인덱스 찾기
    col_map = {}
    for m_label, m_val in months_dict.items():
        for i, cell in enumerate(header_row):
            if str(float(m_val)) in str(cell):
                col_map[m_label] = i
                break
    
    # 검색할 대상 매핑 (사용자 정의 계층 구조)
    # 엑셀의 Unnamed: 3 (index 3) 열의 텍스트와 매칭합니다.
    mapping = {
        "온리프 BU": {
            "전체": {"매출": "온리프 BU (병원+앤파트너스) 매출", "영업이익": "온리프 BU (병원+앤파트너스) 영업이익"},
            "온리프 성형외과": {"매출": "온리프의원 매출", "영업이익": "온리프의원 영업이익"},
            "온리프앤파트너스": {"매출": "온리프앤파트너스 매출", "영업이익": "온리프앤파트너스 영업이익"}
        },
        "르샤인 BU": {
            "전체": {"매출": "르샤인 BU (병원+앤파트너스) 매출", "영업이익": "르샤인 BU (병원+앤파트너스) 영업이익"},
            "르샤인 성형외과": {"매출": "르샤인의원 매출", "영업이익": "르샤인의원 영업이익"},
            "르샤인앤파트너스": {"매출": "르샤인앤파트너스 매출", "영업이익": "르샤인앤파트너스 영업이익"}
        },
        "오블리브 BU": {
            "전체": {"매출": "오블리브 BU (병원+앤파트너스) 매출", "영업이익": "오블리브 BU (병원+앤파트너스) 영업이익"},
            "오블리브 성형외과": {"매출": "오블리브(송도) 매출", "영업이익": "오블리브(송도) 영업이익"},
            "오블리브앤파트너스": {"매출": "오블리브앤파트너스(송도) 매출", "영업이익": "오블리브앤파트너스(송도) 영업이익"}
        }
    }
    
    return df, col_map, mapping

try:
    df, col_map, mapping = load_full_data()
    name_col = df.iloc[:, 3].astype(str).str.replace(" ", "").str.replace("\n", "")
    
    # --- 사이드바 구성 ---
    st.sidebar.header("🔍 검색 필터")
    
    # 1. 월 선택 (다중 선택 가능)
    all_months = list(col_map.keys())
    selected_months = st.sidebar.multiselect("📅 조회 월 선택", all_months, default=all_months)
    
    st.sidebar.separator()
    
    # 2. BU 선택
    selected_main_bu = st.sidebar.selectbox("🏢 BU 선택", list(mapping.keys()))
    
    # 3. 상세 구분 선택 (BU 선택에 따라 변경)
    sub_options = list(mapping[selected_main_bu].keys())
    selected_sub = st.sidebar.selectbox("📍 상세 구분", sub_options)
    
    # --- 데이터 추출 로직 ---
    target_rows = mapping[selected_main_bu][selected_sub]
    final_data = []
    
    for category, row_name in target_rows.items():
        # 키워드로 행 찾기
        clean_row_name = row_name.replace(" ", "")
        match_idx = name_col[name_col.str.contains(clean_row_name, na=False)].index
        
        if not match_idx.empty:
            row_idx = match_idx[0]
            for m in selected_months:
                c_idx = col_map[m]
                val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                val = val if pd.notnull(val) else 0
                final_data.append({
                    "월": m,
                    "구분": category,
                    "금액": val / 1000000
                })
    
    plot_df = pd.DataFrame(final_data)
    
    # --- 메인 화면 표시 ---
    st.title(f"🚀 {selected_main_bu} 실적 현황")
    st.info(f"조회 대상: {selected_sub} | 기간: {selected_months[0]} ~ {selected_months[-1]}")
    
    if not plot_df.empty:
        # 색상 설정 (온리프: 파랑, 르샤인: 초록, 오블리브: 갈색)
        color_map = {"온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
        theme_color = color_map[selected_main_bu]

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 매출 추이 (백만 원)")
            rev_df = plot_df[plot_df["구분"] == "매출"]
            fig_rev = px.line(rev_df, x="월", y="금액", markers=True, text=rev_df["금액"].apply(lambda x: f"{x:,.0f}"))
            fig_rev.update_traces(line_color=theme_color, textposition="top center")
            fig_rev.update_xaxes(type='category')
            st.plotly_chart(fig_rev, use_container_width=True)
            
        with col2:
            st.subheader("💰 영업이익 추이 (백만 원)")
            profit_df = plot_df[plot_df["구분"] == "영업이익"]
            fig_profit = px.bar(profit_df, x="월", y="금액", text=profit_df["금액"].apply(lambda x: f"{x:,.0f}"))
            fig_profit.update_traces(marker_color=theme_color, textposition="outside")
            fig_profit.update_xaxes(type='category')
            fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
            st.plotly_chart(fig_profit, use_container_width=True)

        st.divider()
        
        # 데이터 표
        st.subheader("📝 상세 수치 데이터")
        pivot_df = plot_df.pivot_table(index="구분", columns="월", values="금액")
        st.dataframe(pivot_df.style.format("{:,.0f}"))

    else:
        st.warning("선택한 조건에 맞는 데이터를 엑셀에서 찾을 수 없습니다. 행 이름을 확인해 주세요.")

except Exception as e:
    st.error(f"대시보드 로딩 중 오류가 발생했습니다: {e}")
