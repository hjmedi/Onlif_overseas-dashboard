import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 데이터 로드 함수 (BU 선택에 따라 시트를 다르게 로드)
@st.cache_data
def load_bu_data(selected_bu):
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    
    # BU별 시트 이름 매핑
    sheet_mapping = {
        "온리프 BU": "온리프_실적",
        "르샤인 BU": "르샤인_실적",
        "오블리브 BU": "오블리브(송도)_실적"
    }
    
    target_sheet = sheet_mapping.get(selected_bu)
    
    # 해당 시트 로드
    df = pd.read_excel(file_name, sheet_name=target_sheet)
    
    # 헤더 행(index 3)에서 월 정보 추출
    header_row = df.iloc[3]
    months_dict = {
        "25.01": 2501, "25.02": 2502, "25.03": 2503, "25.04": 2504, "25.05": 2505, "25.06": 2506, 
        "25.07": 2507, "25.08": 2508, "25.09": 2509, "25.10": 2510, "25.11": 2511, "25.12": 2512, 
        "26.01": 2601, "26.02": 2602
    }
    
    col_map = {}
    for m_label, m_val in months_dict.items():
        for i, cell in enumerate(header_row):
            if str(float(m_val)) in str(cell):
                col_map[m_label] = i
                break
                
    return df, col_map

# 3. 사이드바 구성
st.sidebar.header("🔍 경영 실적 필터")

# BU 선택 (가장 먼저 선택해야 시트를 읽어옴)
selected_main_bu = st.sidebar.selectbox("🏢 대상 BU", ["온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    # 선택된 BU에 맞는 시트 로드
    df, col_map = load_bu_data(selected_main_bu)
    name_col = df.iloc[:, 3].astype(str).str.replace(" ", "").str.replace("\n", "")

    # 조회 월 선택
    all_months = list(col_map.keys())
    selected_months = st.sidebar.multiselect("📅 조회 기간 (월)", all_months, default=all_months)
    
    st.sidebar.divider()

    # 상세 구분 키워드 설정 (시트 내에서 행을 찾기 위한 키워드)
    sub_mapping = {
        "전체 (BU 합계)": "BU(병원+앤파트너스)",
        "성형외과 (의원)": "의원",
        "앤파트너스 (법인)": "파트너스"
    }
    selected_sub = st.sidebar.selectbox("📍 상세 실적 구분", list(sub_mapping.keys()))

    # --- 데이터 추출 ---
    if not selected_months:
        st.warning("왼쪽 필터에서 조회할 월을 선택해 주세요.")
    else:
        # '매출'과 '영업이익' 행 찾기
        categories = ["매출", "영업이익"]
        sub_keyword = sub_mapping[selected_sub]
        
        final_data = []
        for cat in categories:
            # 예: '의원'과 '매출'이 동시에 포함된 행 찾기
            match_idx = name_col[name_col.str.contains(sub_keyword, na=False) & name_col.str.contains(cat, na=False)].index
            
            if not match_idx.empty:
                row_idx = match_idx[0]
                for m in selected_months:
                    c_idx = col_map[m]
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    val = val if pd.notnull(val) else 0
                    final_data.append({"월": m, "구분": cat, "금액": val / 1000000})

        plot_df = pd.DataFrame(final_data)

        # --- 메인 화면 ---
        st.title(f"📊 {selected_main_bu} 실적 리포트")
        st.markdown(f"### `{selected_sub}` 실적 분석 (시트: {selected_main_bu.split()[0]}_실적)")
        
        if not plot_df.empty:
            color_map = {"온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오글리브 BU": "#8B4513"}
            theme_color = color_map.get(selected_main_bu, "#31333F")

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
            with st.expander("🔍 데이터 테이블 확인"):
                st.dataframe(plot_df.pivot_table(index="구분", columns="월", values="금액").style.format("{:,.0f}"))
        else:
            st.error(f"'{selected_sub}'에 해당하는 '{categories}' 데이터를 시트에서 찾을 수 없습니다. 엑셀의 행 이름을 확인해 주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
