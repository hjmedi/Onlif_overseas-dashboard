import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 전사 경영 실적", layout="wide")

st.title("🚀 메디빌더 그룹 경영 실적 추이 (2025 - 2026.02)")
st.markdown("#### 엑셀 마스터 파일을 기반으로 한 통합 실적 현황입니다.")

# 2. 데이터 로드 함수 (엑셀 버전)
@st.cache_data
def load_data():
    # 엑셀 파일명 (확장자 .xlsx 확인)
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    
    # 엑셀의 '통합_경영레포트' 시트를 읽어옵니다.
    # engine='openpyxl'은 엑셀 파일을 읽기 위해 필요합니다.
    df = pd.read_excel(file_name, sheet_name="통합_경영레포트")
    
    # 데이터 추출 위치 (아까 검증한 인덱스 그대로 사용)
    # 2501~2512(56~67열), 2601~2602(69, 70열)
    cols_idx = list(range(56, 68)) + [69, 70]
    months = ["25.01", "25.02", "25.03", "25.04", "25.05", "25.06", 
              "25.07", "25.08", "25.09", "25.10", "25.11", "25.12", "26.01", "26.02"]

    targets = {
        "온리프_매출": 10, "온리프_영업이익": 11,   # 인덱스 재확인: 실제 행 번호에 따라 조정 필요할 수 있음
        "르샤인_매출": 19, "르샤인_영업이익": 20,
        "오블리브_매출": 28, "오블리브_영업이익": 29
    }
    
    # 엑셀 파일의 경우 헤더 위치에 따라 행 번호가 CSV와 1~2줄 차이날 수 있습니다.
    # 만약 그래프가 이상하면 이 숫자들을 다시 조정해 드릴게요.

    final_list = []
    for key, row_idx in targets.items():
        unit, category = key.split("_")
        # 엑셀 데이터에서 해당 행/열 값 추출
        vals = pd.to_numeric(df.iloc[row_idx, cols_idx], errors='coerce').tolist()
        for month, val in zip(months, vals):
            final_list.append({"사업부": unit, "구분": category, "월": month, "금액": val})
            
    return pd.DataFrame(final_list)

try:
    df_plot = load_data()
    order = ["온리프", "르샤인", "오블리브"]

    # --- 매출 추이 ---
    st.subheader("📈 사업부별 매출 추이")
    rev_df = df_plot[df_plot["구분"] == "매출"]
    fig_rev = px.line(rev_df, x="월", y="금액", color="사업부", 
                      category_orders={"사업부": order}, markers=True)
    st.plotly_chart(fig_rev, use_container_width=True)

    st.divider()

    # --- 영업이익 추이 ---
    st.subheader("💰 사업부별 영업이익 추이")
    profit_df = df_plot[df_plot["구분"] == "영업이익"]
    fig_profit = px.bar(profit_df, x="월", y="금액", color="사업부", 
                        barmode="group", category_orders={"사업부": order})
    fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
    st.plotly_chart(fig_profit, use_container_width=True)

except Exception as e:
    st.error(f"에러 발생: {e}")
    st.info("엑셀 파일이 깃허브에 업로드되어 있는지, 시트 이름이 '통합_경영레포트'가 맞는지 확인해 주세요.")
