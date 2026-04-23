import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 전사 경영 실적", layout="wide")
st.title("🚀 메디빌더 그룹 경영 실적 추이 (2025 - 2026.02)")

@st.cache_data
def load_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    header_row = df.iloc[3]
    months_dict = {
        "25.01": 2501, "25.02": 2502, "25.03": 2503, "25.04": 2504, "25.05": 2505, "25.06": 2506, 
        "25.07": 2507, "25.08": 2508, "25.09": 2509, "25.10": 2510, "25.11": 2511, "25.12": 2512, 
        "26.01": 2601, "26.02": 2602
    }
    
    col_indices = []
    for m_label, m_val in months_dict.items():
        found_idx = -1
        for i, cell in enumerate(header_row):
            if str(float(m_val)) in str(cell):
                found_idx = i
                break
        col_indices.append(found_idx)

    targets = {
        "온리프_매출": "온리프 매출", "온리프_영업이익": "온리프 영업이익",
        "르샤인_매출": "르샤인 매출", "르샤인_영업이익": "르샤인 영업이익",
        "오블리브_매출": "오블리브(송도) 매출", "오블리브_영업이익": "오블리브(송도) 영업이익"
    }

    final_list = []
    name_col = df.iloc[:, 3].astype(str).str.strip()

    for key, target_name in targets.items():
        unit, category = key.split("_")
        match_idx = name_col[name_col == target_name].index
        if match_idx.empty:
            match_idx = name_col[name_col.str.contains(target_name, na=False, regex=False)].index
        
        if not match_idx.empty:
            row_idx = match_idx[0]
            for m_label, c_idx in zip(months_dict.keys(), col_indices):
                if c_idx != -1:
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    val = val if pd.notnull(val) else 0
                    # ⭐ 금액을 1,000,000으로 나누어 '백만 원' 단위로 변환
                    final_list.append({"사업부": unit, "구분": category, "월": m_label, "금액": val / 1000000})
                else:
                    final_list.append({"사업부": unit, "구분": category, "월": m_label, "금액": 0})
            
    return pd.DataFrame(final_list)

try:
    df_plot = load_data()
    month_order = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", "25.07", "25.08", "25.09", "25.10", "25.11", "25.12", "26.01", "26.02"]
    unit_order = ["온리프", "르샤인", "오블리브"]

    if not df_plot.empty:
        # 1. 매출 추이 그래프
        st.subheader("📈 사업부별 매출 추이 (단위: 백만 원)")
        rev_df = df_plot[df_plot["구분"] == "매출"]
        fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", 
                          category_orders={"월": month_order, "사업부": unit_order}, 
                          markers=True,
                          labels={"금액": "매출액 (백만 원)"},
                          color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        fig_rev.update_xaxes(type='category')
        fig_rev.update_layout(yaxis_tickformat=",d") # 천 단위 콤마
        st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # 2. 영업이익 추이 그래프
        st.subheader("💰 사업부별 영업이익 추이 (단위: 백만 원)")
        profit_df = df_plot[df_plot["구분"] == "영업이익"]
        fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", 
                            barmode="group", 
                            category_orders={"월": month_order, "사업부": unit_order},
                            labels={"금액": "영업이익 (백만 원)"},
                            color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        fig_profit.update_xaxes(type='category')
        fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_profit, use_container_width=True)

        # 3. 데이터 검증 표
        with st.expander("📝 수치 데이터 확인 (단위: 백만 원)"):
            pivot_df = df_plot.pivot_table(index=["사업부", "구분"], columns="월", values="금액")
            pivot_df = pivot_df[month_order]
            st.dataframe(pivot_df.style.format("{:,.0f}"))
            
    else:
        st.error("데이터를 찾을 수 없습니다.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
