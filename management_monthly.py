import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="메디빌더 전사 경영 실적", layout="wide")
st.title("🚀 메디빌더 그룹 경영 실적 추이 (2025 - 2026.02)")

@st.cache_data
def load_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    # 시트 로드
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    # [열 찾기] 2501.0 부터 2602.0 까지 들어있는 열 위치를 자동으로 찾습니다.
    # 엑셀 상단에 2501, 2502... 숫자가 있는 행을 기준으로 인덱스를 따냅니다.
    months_map = {
        "25.01": 2501, "25.02": 2502, "25.03": 2503, "25.04": 2504, "25.05": 2505, "25.06": 2506, 
        "25.07": 2507, "25.08": 2508, "25.09": 2509, "25.10": 2510, "25.11": 2511, "25.12": 2512, 
        "26.01": 2601, "26.02": 2602
    }
    
    # 실제 데이터가 시작되는 행(계정과목 행) 찾기
    header_row_idx = 3 # 엑셀상 4번째 줄에 계정과목이 있다고 가정
    header_row = df.iloc[header_row_idx]
    
    col_indices = []
    for m_label, m_code in months_map.items():
        # 열 헤더에서 해당 월 코드를 찾음 (숫자나 문자열 모두 대응)
        found_col = -1
        for i, cell in enumerate(header_row):
            if str(m_code) in str(cell):
                found_col = i
                break
        col_indices.append(found_col)

    # [행 찾기] 띄어쓰기 무시하고 키워드로 행을 찾습니다.
    targets = {
        "온리프_매출": "온리프매출", "온리프_영업이익": "온리프영업이익",
        "르샤인_매출": "르샤인매출", "르샤인_영업이익": "르샤인영업이익",
        "오블리브_매출": "오블리브(송도)매출", "오블리브_영업이익": "오블리브(송도)영업이익"
    }

    final_list = []
    # 4번째 열(Unnamed: 3)이 보통 계정명이 들어있는 곳입니다.
    name_column = df.iloc[:, 3].astype(str).str.replace(" ", "").str.replace("\n", "")

    for key, search_keyword in targets.items():
        unit, category = key.split("_")
        
        # 키워드가 포함된 행 인덱스 추출
        match_idx = name_column[name_column.str.contains(search_keyword, na=False)].index
        
        if not match_idx.empty:
            row_idx = match_idx[0]
            # 해당 행에서 찾은 열들의 수치를 가져옴
            row_values = []
            for c_idx in col_indices:
                if c_idx != -1:
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    row_values.append(val if pd.notnull(val) else 0)
                else:
                    row_values.append(0)
            
            for m_label, v in zip(months_map.keys(), row_values):
                final_list.append({"사업부": unit, "구분": category, "월": m_label, "금액": v})
            
    return pd.DataFrame(final_list)

try:
    df_plot = load_data()
    order = ["온리프", "르샤인", "오블리브"]

    if not df_plot.empty:
        # 매출 그래프
        st.subheader("📈 사업부별 매출 추이")
        rev_df = df_plot[df_plot["구분"] == "매출"]
        fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", 
                          category_orders={"사업부": order}, markers=True,
                          color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        fig_rev.update_layout(yaxis_tickformat=",d") # 숫자 콤마 표시
        st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # 영업이익 그래프
        st.subheader("💰 사업부별 영업이익 추이")
        profit_df = df_plot[df_plot["구분"] == "영업이익"]
        fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", 
                            barmode="group", category_orders={"사업부": order},
                            color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
        fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_profit, use_container_width=True)

        # 상세 데이터 표 (검증용)
        with st.expander("📝 추출된 원본 수치 확인"):
            st.dataframe(df_plot.pivot_table(index=["사업부", "구분"], columns="월", values="금액").style.format("{:,.0f}"))
    else:
        st.error("데이터를 하나도 찾지 못했습니다. 엑셀 파일의 '통합_경영레포트' 시트에 값이 있는지 확인해 주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
