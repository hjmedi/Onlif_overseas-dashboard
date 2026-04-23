import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

@st.cache_data
def load_bu_data(selected_bu):
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    sheet_mapping = {"온리프 BU": "온리프_실적", "르샤인 BU": "르샤인_실적", "오블리브 BU": "오블리브(송도)_실적"}
    target_sheet = sheet_mapping.get(selected_bu)
    df = pd.read_excel(file_name, sheet_name=target_sheet)
    
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}
    
    col_map = {}
    header_row_idx = -1
    for idx in range(min(15, len(df))):
        row = df.iloc[idx]
        if any("2501" in str(cell) for cell in row if pd.notnull(cell)):
            header_row_idx = idx
            break
            
    if header_row_idx != -1:
        header_row = df.iloc[header_row_idx]
        for m_label, m_val in months_dict.items():
            for i, cell in enumerate(header_row):
                if pd.notnull(cell) and m_val in str(cell).replace(".0", ""):
                    col_map[m_label] = i
                    break
    return df, col_map

st.sidebar.header("🔍 경영 실적 필터")
selected_main_bu = st.sidebar.selectbox("🏢 대상 BU", ["온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    df, col_map = load_bu_data(selected_main_bu)
    all_months = list(col_map.keys()) if col_map else []
    selected_months = st.sidebar.multiselect("📅 조회 기간 (월)", all_months, default=all_months)
    
    st.sidebar.divider()
    # 검색 키워드를 더 단순하게 수정했습니다.
    sub_mapping = {
        "전체 (BU 합계)": "BU", 
        "성형외과 (의원)": "의원",
        "앤파트너스 (법인)": "파트너스"
    }
    selected_sub = st.sidebar.selectbox("📍 상세 실적 구분", list(sub_mapping.keys()))

    if not selected_months:
        st.warning("왼쪽 필터에서 조회할 월을 선택해 주세요.")
    else:
        # D열(index 3) 데이터를 가져옴
        name_col_raw = df.iloc[:, 3].fillna("").astype(str)
        name_col_clean = name_col_raw.str.replace(" ", "").str.replace("\n", "")
        
        categories = ["매출", "영업이익"]
        sub_keyword = sub_mapping[selected_sub]
        final_data = []

        for cat in categories:
            # 1차 시도: 키워드 조합 검색
            match_idx = name_col_clean[name_col_clean.str.contains(sub_keyword, na=False) & name_col_clean.str.contains(cat, na=False)].index
            
            # 2차 시도: 실패 시 '매출' 단어만이라도 찾기
            if match_idx.empty:
                match_idx = name_col_clean[name_col_clean.str.contains(cat, na=False)].index

            if not match_idx.empty:
                row_idx = match_idx[0]
                for m in selected_months:
                    c_idx = col_map[m]
                    val = pd.to_numeric(df.iloc[row_idx, c_idx], errors='coerce')
                    final_data.append({"월": m, "구분": cat, "금액": (val if pd.notnull(val) else 0) / 1000000})

        plot_df = pd.DataFrame(final_data)

        st.title(f"📊 {selected_main_bu} 실적 리포트")
        
        if not plot_df.empty:
            # 그래프 그리기 (기존 코드와 동일)
            color_map = {"온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
            theme_color = color_map.get(selected_main_bu, "#31333F")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📈 매출 추이 (백만 원)")
                fig_rev = px.line(plot_df[plot_df["구분"]=="매출"], x="월", y="금액", markers=True, text=plot_df[plot_df["구분"]=="매출"]["금액"].apply(lambda x: f"{x:,.0f}"))
                fig_rev.update_traces(line_color=theme_color, textposition="top center")
                st.plotly_chart(fig_rev, use_container_width=True)
            with c2:
                st.subheader("💰 영업이익 추이 (백만 원)")
                fig_profit = px.bar(plot_df[plot_df["구분"]=="영업이익"], x="월", y="금액", text=plot_df[plot_df["구분"]=="영업이익"]["금액"].apply(lambda x: f"{x:,.0f}"))
                fig_profit.update_traces(marker_color=theme_color, textposition="outside")
                st.plotly_chart(fig_profit, use_container_width=True)
        else:
            st.error("데이터를 찾을 수 없습니다.")
            # 💡 [핵심] 데이터를 못 찾았을 때, 엑셀에 어떤 이름들이 있는지 보여줍니다.
            with st.expander("🛠️ 문제 해결: 엑셀에 있는 행 이름들 확인하기"):
                st.write("현재 코드에서 감지한 엑셀 D열의 이름들입니다. 이 중에서 어떤 걸 가져와야 할까요?")
                st.write(name_col_raw.unique().tolist())

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
