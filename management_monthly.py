import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 전사 경영 실적", layout="wide")
st.title("🚀 메디빌더 그룹 경영 실적 추이 (2025 - 2026.02)")

@st.cache_data
def load_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    # 시트 로드
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    # [열 찾기] 엑셀의 헤더 행(index 3)에서 월별 열 위치를 정확히 찾습니다.
    header_row = df.iloc[3]
    
    # 2501 ~ 2602 데이터 열 인덱스 추출
    months_dict = {
        "25.01": 2501, "25.02": 2502, "25.03": 2503, "25.04": 2504, "25.05": 2505, "25.06": 2506, 
        "25.07": 2507, "25.08": 2508, "25.09": 2509, "25.10": 2510, "25.11": 2511, "25.12": 2512, 
        "26.01": 2601, "26.02": 2602
    }
    
    col_indices = []
    for m_label, m_val in months_dict.items():
        found_idx = -1
        for i, cell in enumerate(header_row):
            # 숫자로 되어있는 열 헤더와 비교
            if str(float(m_val)) in str(cell):
                found_idx = i
                break
        col_indices.append(found_idx)

    # [행 찾기] 실제 엑셀에 적힌 정확한 이름으로 매칭합니다.
    # 괄호()가 포함되어 있어도 검색이 가능하도록 설정했습니다.
    targets = {
        "온리프_매출": "온리프 매출", "온리프_영업이익": "온리프 영업이익",
        "르샤인_매출": "르샤인 매출", "르샤인_영업이익": "르샤인 영업이익",
        "오블리브_매출": "오블리브(송도) 매출", "오블리브_영업이익": "오블리브(송도) 영업이익"
    }

    final_list = []
    # 4번째 열(Unnamed: 3)에서 이름 찾기
    name_col = df.iloc[:, 3].astype(str).str.strip()

    for key, target_name in targets.items():
        unit, category = key.split("_")
        
        # regex=False 설정을 통해 괄호()를 문자로 인식하게 함 (핵심 수정 사항)
        match_idx = name_col[name_col.str.contains(target_name, na=False, regex=False)].index
        
        if not match_idx.empty:
            row_idx = match_idx[0]
            # 수치 데이터 추출
            row_vals = []
            for c_idx in col_indices:
                if c_idx != -1:
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    row_vals.append(val if pd.notnull(val) else 0)
                else:
                    row_vals.append(0)
            
            for m_label, v in zip(months_dict.keys(), row_vals):
                final_list.append({"사업부": unit, "구분": category, "월": m_label, "금액": v})
            
    return pd.DataFrame(final_list)

try:
    df_plot = load_data()
    order = ["온리프", "르샤인", "오블리브"]

    if not df_plot.empty:
        # 1. 매출 추이 그래프
        st.subheader("📈 사업부별 매출 추이")
        rev_df = df_plot[df_plot["구분"] == "매출"]
        fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", 
                          category_orders={"사업부": order}, markers=True,
                          color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # 2. 영업이익 추이 그래프
        st.subheader("💰 사업부별 영업이익 추이")
        profit_df = df_plot[df_plot["구분"] == "영업이익"]
        fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", 
                            barmode="group", category_orders={"사업부": order},
                            color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_profit, use_container_width=True)

        # 3. 상세 데이터 표
        with st.expander("📝 월별 데이터 요약"):
            st.dataframe(df_plot.pivot_table(index=["사업부", "구분"], columns="월", values="금액").style.format("{:,.0f}"))
    else:
        st.error("데이터를 불러오지 못했습니다. 파일 구조를 다시 확인해 주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
