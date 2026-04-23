import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 데이터 로드 및 정밀 행 추출 함수
@st.cache_data
def load_bu_data(selected_bu):
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    
    # BU별 시트 및 날짜 헤더 행 설정
    bu_configs = {
        "온리프 BU": {"sheet": "온리프_실적", "header_row": 6-1},
        "르샤인 BU": {"sheet": "르샤인_실적", "header_row": 5-1},
        "오블리브 BU": {"sheet": "오블리브(송도)_실적", "header_row": 6-1}
    }
    
    config = bu_configs[selected_bu]
    # 좌표 계산을 위해 header=None으로 로드
    df = pd.read_excel(file_name, sheet_name=config["sheet"], header=None)
    
    # 날짜 열(2501~2602) 위치 매핑
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

# 3. 사이드바 필터 구성
st.sidebar.header("🔍 경영 실적 필터")
selected_main_bu = st.sidebar.selectbox("🏢 대상 BU", ["온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    df, col_map = load_bu_data(selected_main_bu)
    all_months = list(col_map.keys())
    selected_months = st.sidebar.multiselect("📅 조회 기간 (월)", all_months, default=all_months)
    
    st.sidebar.divider()

    # --- 사용자 제공 최신 행 번호 매핑 (Excel 행 번호 - 1) ---
    if selected_main_bu == "온리프 BU":
        row_mapping = {
            "전체 (BU 합계)": {"매출": 25-1, "영업이익": 52-1},
            "온리프 성형외과": {"매출": 77-1, "영업이익": 116-1},
            "온리프앤파트너스": {"매출": 121-1, "영업이익": 155-1} # 최신 수정 반영
        }
    elif selected_main_bu == "르샤인 BU":
        row_mapping = {
            "전체 (BU 합계)": {"매출": 36-1, "영업이익": 60-1}, 
            "르샤인 클리닉": {"매출": 85-1, "영업이익": 127-1},
            "르샤인앤파트너스": {"매출": 132-1, "영업이익": 163-1}
        }
    else: # 오블리브 BU
        row_mapping = {
            "전체 (BU 합계)": {"매출": 34-1, "영업이익": 58-1},
            "오블리브 의원": {"매출": 83-1, "영업이익": 125-1},
            "오블리브앤파트너스": {"매출": 130-1, "영업이익": 163-1}
        }

    selected_sub = st.sidebar.selectbox("📍 상세 실적 구분", list(row_mapping.keys()))

    if not selected_months:
        st.warning("왼쪽 필터에서 조회할 월을 선택해 주세요.")
    else:
        target_rows = row_mapping[selected_sub]
        final_data = []
        
        for category, row_idx in target_rows.items():
            for m in selected_months:
                if m in col_map:
                    c_idx = col_map[m]
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    val = val if pd.notnull(val) else 0
                    final_data.append({"월": m, "구분": category, "금액": val / 1000000})

        plot_df = pd.DataFrame(final_data)

        # --- 메인 화면 출력 ---
        st.title(f"📊 {selected_main_bu} 실적 리포트")
        st.markdown(f"### `{selected_sub}` 실적 분석")
        
        if not plot_df.empty:
            color_map = {"온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
            theme_color = color_map.get(selected_main_bu, "#31333F")

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📈 매출 추이 (백만 원)")
                rev_df = plot_df[plot_df["구분"] == "매출"]
                fig_rev = px.line(rev_df, x="월", y="금액", markers=True, 
                                  text=rev_df["금액"].apply(lambda x: f"{x:,.0f}"))
                fig_rev.update_traces(line_color=theme_color, textposition="top center")
                fig_rev.update_xaxes(type='category')
                st.plotly_chart(fig_rev, use_container_width=True)
                
            with c2:
                st.subheader("💰 영업이익 추이 (백만 원)")
                profit_df = plot_df[plot_df["구분"] == "영업이익"]
                fig_profit = px.bar(profit_df, x="월", y="금액", 
                                    text=profit_df["금액"].apply(lambda x: f"{x:,.0f}"))
                fig_profit.update_traces(marker_color=theme_color, textposition="outside")
                fig_profit.update_xaxes(type='category')
                fig_profit.add_hline(y=0, line_dash="dash", line_color="black")
                st.plotly_chart(fig_profit, use_container_width=True)
            
            st.divider()
            with st.expander("📝 상세 데이터 확인 (단위: 백만 원)"):
                st.dataframe(plot_df.pivot_table(index="구분", columns="월", values="금액").style.format("{:,.0f}"))
        else:
            st.error("데이터를 추출하지 못했습니다. 행 번호를 다시 확인해 주세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
