import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

st.title("📊 그룹사 경영 실적 추이 (2025 ~ 2026.02)")
st.info("통합 경영관리 마스터 파일을 기반으로 한 온리프, 르샤인, 오블리브 실적 현황입니다.")

# 2. 데이터 로드
@st.cache_data
def load_management_data():
    # 업로드하신 파일명과 일치해야 합니다.
    file_path = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx - 통합_경영레포트.csv"
    df = pd.read_csv(file_path)
    
    # 2025년 1월 ~ 2026년 2월 열 인덱스 (파일 구조 기반)
    cols_2025 = list(range(56, 68)) # 2501 ~ 2512
    cols_2026 = [69, 70] # 2601 ~ 2602
    all_cols = cols_2025 + cols_2026
    
    months = [
        "25.01", "25.02", "25.03", "25.04", "25.05", "25.06",
        "25.07", "25.08", "25.09", "25.10", "25.11", "25.12",
        "26.01", "26.02"
    ]

    # 대상 행 (인덱스 기준) - 온리프, 르샤인, 오블리브 순서
    targets = {
        "온리프_매출": 13, "온리프_영업이익": 14,
        "르샤인_매출": 22, "르샤인_영업이익": 23,
        "오블리브_매출": 31, "오블리브_영업이익": 32
    }

    processed_data = []
    for key, idx in targets.items():
        unit, type_name = key.split("_")
        values = df.iloc[idx, all_cols].values
        # 숫자형 변환
        values = pd.to_numeric(values, errors='coerce').tolist()
        
        for month, val in zip(months, values):
            processed_data.append({
                "사업부": unit,
                "구분": type_name,
                "월": month,
                "금액": val
            })
            
    return pd.DataFrame(processed_data)

try:
    df_clean = load_management_data()
    order = ["온리프", "르샤인", "오블리브"]
    
    st.divider()

    # --- 매출 추이 그래프 ---
    st.subheader("📈 사업부별 매출 추이 (단위: 원)")
    rev_df = df_clean[df_clean["구분"] == "매출"]
    fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", 
                      category_orders={"사업부": order},
                      markers=True,
                      color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
    st.plotly_chart(fig_rev, use_container_width=True)

    # --- 영업이익 추이 그래프 ---
    st.subheader("💰 사업부별 영업이익 추이 (단위: 원)")
    profit_df = df_clean[df_clean["구분"] == "영업이익"]
    fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", 
                        barmode="group", category_orders={"사업부": order},
                        color_discrete_map={"온리프": "#1f77b4", "르샤인": "#ff7f0e", "오블리브": "#2ca02c"})
    fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_profit, use_container_width=True)

    # 상세 데이터 표
    with st.expander("🔍 월별 상세 데이터 확인"):
        pivot_df = df_clean.pivot_table(index=["사업부", "구분"], columns="월", values="금액")
        st.dataframe(pivot_df.style.format("{:,.0f}"))

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 파일이 GitHub에 있는지 확인해 주세요.")
