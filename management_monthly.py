import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="메디빌더 전사 경영 실적", layout="wide")
st.title("🚀 메디빌더 그룹 경영 실적 추이 (2025 - 2026.02)")

@st.cache_data
def load_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    # 시트 이름을 '통합_경영레포트'로 읽기
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    # 2501(56번열)~2602(70번열)까지의 열 인덱스 (엑셀 구조에 맞춰 자동 조정)
    # 엑셀은 0부터 시작하므로 CSV보다 인덱스가 정확히 일치하는지 확인 필요
    cols_idx = list(range(56, 68)) + [69, 70] 
    months = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
              "25.07", "25.08", "25.09", "25.10", "25.11", "25.12", "26.01", "26.02"]

    # 행 이름을 찾아서 매칭 (숫자 대신 이름으로 찾기)
    targets = {
        "온리프_매출": "온리프 매출", "온리프_영업이익": "온리프 영업이익",
        "르샤인_매출": "르샤인 매출", "르샤인_영업이익": "르샤인 영업이익",
        "오블리브_매출": "오블리브(송도) 매출", "오블리브_영업이익": "오블리브(송도) 영업이익"
    }

    final_list = []
    for key, target_name in targets.items():
        unit, category = key.split("_")
        # 해당 이름이 들어있는 행 찾기
        row = df[df.iloc[:, 3].astype(str).str.contains(target_name, na=False)]
        
        if not row.empty:
            vals = pd.to_numeric(row.iloc[0, cols_idx], errors='coerce').tolist()
            for month, val in zip(months, vals):
                final_list.append({"사업부": unit, "구분": category, "월": month, "금액": val})
            
    return pd.DataFrame(final_list)

try:
    df_plot = load_data()
    order = ["온리프", "르샤인", "오블리브"]

    if not df_plot.empty:
        # 매출 그래프
        st.subheader("📈 사업부별 매출 추이")
        rev_df = df_plot[df_plot["구분"] == "매출"]
        fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", category_orders={"사업부": order}, markers=True)
        st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # 영업이익 그래프
        st.subheader("💰 사업부별 영업이익 추이")
        profit_df = df_plot[df_plot["구분"] == "영업이익"]
        fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", barmode="group", category_orders={"사업부": order})
        fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_profit, use_container_width=True)
    else:
        st.warning("데이터를 찾을 수 없습니다. 엑셀 파일의 양식을 확인해 주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
