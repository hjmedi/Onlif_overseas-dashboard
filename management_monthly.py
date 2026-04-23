import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# 2. 데이터 로드 함수
@st.cache_data
def load_all_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    sheets = {"HQ": "HQ_실적", "온리프": "온리프_실적", "르샤인": "르샤인_실적", "오블리브": "오블리브(송도)_실적"}
    header_rows = {"HQ": 5-1, "온리프": 6-1, "르샤인": 5-1, "오블리브": 6-1}
    
    data_frames, col_maps = {}, {}
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}

    for key, s_name in sheets.items():
        try:
            df = pd.read_excel(file_name, sheet_name=s_name, header=None)
            data_frames[key] = df
            h_row = df.iloc[header_rows[key]]
            c_map = {m_l: i for m_l, m_v in months_dict.items() for i, cell in enumerate(h_row) if str(m_v) in str(cell).replace(".0", "")}
            col_maps[key] = c_map
        except: st.error(f"시트 '{s_name}' 로드 실패")
    return data_frames, col_maps

def get_val(df, row, col):
    if col is None or pd.isna(col): return 0
    v = pd.to_numeric(df.iloc[row, col], errors='coerce')
    return (v if pd.notnull(v) else 0) / 1000000

# 3. 사이드바 구성
st.sidebar.header("🔍 경영 실적 필터")
selected_main_bu = st.sidebar.selectbox("🏢 대상 BU 선택", ["연결 실적(통합)", "병원 실적 비교", "메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    dfs, maps = load_all_data()
    all_months = list(maps["온리프"].keys())
    st.sidebar.markdown("### 📈 기간 설정")
    start_m, end_m = st.sidebar.select_slider("기간 선택", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed")
    selected_months = all_months[all_months.index(start_m) : all_months.index(end_m) + 1]

    # --- [병원 실적 비교 모드] ---
    if selected_main_bu == "병원 실적 비교":
        st.title("⚖️ 병원별 실적 일대일 비교")
        col1, col2 = st.sidebar.columns(2)
        h1_name = col1.selectbox("병원 1", ["온리프 성형외과", "르샤인 클리닉", "오블리브 의원"], index=0)
        h2_name = col2.selectbox("병원 2", ["온리프 성형외과", "르샤인 클리닉", "오블리브 의원"], index=1)

        h_info = {
            "온리프 성형외과": {"key": "온리프", "sales_row": 77-1, "profit_row": 116-1, "color": "#1f77b4"},
            "르샤인 클리닉": {"key": "르샤인", "sales_row": 85-1, "profit_row": 127-1, "color": "#006400"},
            "오블리브 의원": {"key": "오블리브", "sales_row": 83-1, "profit_row": 125-1, "color": "#8B4513"}
        }

        d1, d2 = h_info[h1_name], h_info[h2_name]
        
        # 데이터 추출
        s1 = [get_val(dfs[d1['key']], d1['sales_row'], maps[d1['key']][m]) for m in selected_months]
        p1 = [get_val(dfs[d1['key']], d1['profit_row'], maps[d1['key']][m]) for m in selected_months]
        r1 = [(p/s*100 if s!=0 else 0) for s, p in zip(s1, p1)]

        s2 = [get_val(dfs[d2['key']], d2['sales_row'], maps[d2['key']][m]) for m in selected_months]
        p2 = [get_val(dfs[d2['key']], d2['profit_row'], maps[d2['key']][m]) for m in selected_months]
        r2 = [(p/s*100 if s!=0 else 0) for s, p in zip(s2, p2)]

        # 차트 1: 매출 비교 (Line)
        st.subheader("📈 병원별 매출 추이 비교 (백만 원)")
        fig_s = go.Figure()
        fig_s.add_trace(go.Scatter(x=selected_months, y=s1, name=h1_name, mode='lines+markers+text', line=dict(color=d1['color'], width=4), text=[f"{v:,.0f}" for v in s1], textposition="top center"))
        fig_s.add_trace(go.Scatter(x=selected_months, y=s2, name=h2_name, mode='lines+markers+text', line=dict(color=d2['color'], width=4, dash='dot'), text=[f"{v:,.0f}" for v in s2], textposition="bottom center"))
        fig_s.update_layout(height=450, margin=dict(l=20,r=20,t=20,b=20), hovermode="x unified")
        st.plotly_chart(fig_s, use_container_width=True)

        # 차트 2: 영업이익률 비교 (Bar)
        st.subheader("💰 병원별 영업이익률(%) 비교")
        fig_r = go.Figure()
        fig_r.add_trace(go.Bar(x=selected_months, y=r1, name=f"{h1_name} 이익률", marker_color=d1['color'], opacity=0.7, text=[f"{v:.1f}%" for v in r1], textposition="outside"))
        fig_r.add_trace(go.Bar(x=selected_months, y=r2, name=f"{h2_name} 이익률", marker_color=d2['color'], opacity=0.4, text=[f"{v:.1f}%" for v in r2], textposition="outside"))
        fig_r.update_layout(height=450, barmode='group', margin=dict(l=20,r=20,t=20,b=20), hovermode="x unified")
        fig_r.add_hline(y=0, line_dash="dash", line_color="black")
        st.plotly_chart(fig_r, use_container_width=True)

    # --- 기존 연결 실적 및 개별 BU 로직 (생략/유지) ---
    elif selected_main_bu == "연결 실적(통합)":
        st.title("🌐 메디빌더 그룹 연결 실적 현황")
        # (기존 연결 실적 코드와 동일...)
        total_sales = [get_val(dfs["온리프"], 25-1, maps["온리프"][m]) + get_val(dfs["르샤인"], 36-1, maps["르샤인"][m]) + get_val(dfs["오블리브"], 34-1, maps["오블리브"][m]) for m in selected_months]
        total_profit = [get_val(dfs["온리프"], 52-1, maps["온리프"][m]) + get_val(dfs["르샤인"], 60-1, maps["르샤인"][m]) + get_val(dfs["오블리브"], 58-1, maps["오블리브"][m]) + get_val(dfs["HQ"], 51-1, maps["HQ"][m]) for m in selected_months]
        
        # 공통 차트 함수 활용 (생략된 기존 함수 draw_combo_chart 호출)
        def draw_chart(title, s, p, c):
            fig = go.Figure()
            fig.add_trace(go.Bar(x=selected_months, y=p, name="영업이익", marker_color=c, opacity=0.6, text=[f"{v:,.0f}" for v in p], textposition="outside"))
            fig.add_trace(go.Scatter(x=selected_months, y=s, name="매출", mode="lines+markers+text", line=dict(color="#FF4B4B", width=3), text=[f"{v:,.0f}" for v in s], textposition="top center"))
            fig.update_layout(height=450, margin=dict(l=20,r=20,t=30,b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), xaxis=dict(type='category'))
            st.markdown(f"## {title}"); st.plotly_chart(fig, use_container_width=True)

        draw_chart("📊 그룹 전체 연결 실적", total_sales, total_profit, "#E91E63")
        st.divider()
        corp_sales = [get_val(dfs["HQ"], 14-1, maps["HQ"][m]) + get_val(dfs["온리프"], 121-1, maps["온리프"][m]) + get_val(dfs["르샤인"], 132-1, maps["르샤인"][m]) + get_val(dfs["오블리브"], 130-1, maps["오블리브"][m]) for m in selected_months]
        corp_profit = [get_val(dfs["온리프"], 155-1, maps["온리프"][m]) + get_val(dfs["르샤인"], 163-1, maps["르샤인"][m]) + get_val(dfs["오블리브"], 163-1, maps["오블리브"][m]) + get_val(dfs["HQ"], 51-1, maps["HQ"][m]) for m in selected_months]
        draw_chart("🏢 법인 연결 실적", corp_sales, corp_profit, "#9C27B0")

    else:
        # 개별 BU 로직 (기존 코드 유지)
        st.title(f"🚀 {selected_main_bu} 경영 리포트")
        key_map = {"메디빌더": "HQ", "온리프 BU": "온리프", "르샤인 BU": "르샤인", "오블리브 BU": "오블리브"}
        k = key_map[selected_main_bu]
        color_map = {"메디빌더": "#333333", "온리프 BU": "#1f77b4", "르샤인 BU": "#006400", "오블리브 BU": "#8B4513"}
        if k == "HQ": row_map = {"📊 HQ 실적": {"매출": 14-1, "영익": 51-1}}
        elif k == "온리프": row_map = {"📊 온리프 BU 합계": {"매출": 25-1, "영익": 52-1}, "🏥 온리프 성형외과": {"매출": 77-1, "영익": 116-1}, "🤝 온리프앤파트너스": {"매출": 121-1, "영익": 155-1}}
        elif k == "르샤인": row_map = {"📊 르샤인 BU 합계": {"매출": 36-1, "영익": 60-1}, "🏥 르샤인 클리닉": {"매출": 85-1, "영익": 127-1}, "🤝 르샤인앤파트너스": {"매출": 132-1, "영익": 163-1}}
        else: row_map = {"📊 오블리브 BU 합계": {"매출": 34-1, "영익": 58-1}, "🏥 오블리브 의원": {"매출": 83-1, "영익": 125-1}, "🤝 오블리브앤파트너스": {"매출": 130-1, "영익": 163-1}}
        
        for title, rows in row_map.items():
            s = [get_val(dfs[k], rows["매출"], maps[k][m]) for m in selected_months]
            p = [get_val(dfs[k], rows["영익"], maps[k][m]) for m in selected_months]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=selected_months, y=p, name="영업이익", marker_color=color_map[selected_main_bu], opacity=0.6, text=[f"{v:,.0f}" for v in p], textposition="outside"))
            fig.add_trace(go.Scatter(x=selected_months, y=s, name="매출", mode="lines+markers+text", line=dict(color="#FF4B4B", width=3), text=[f"{v:,.0f}" for v in s], textposition="top center"))
            st.markdown(f"## {title}"); st.plotly_chart(fig, use_container_width=True); st.divider()

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
