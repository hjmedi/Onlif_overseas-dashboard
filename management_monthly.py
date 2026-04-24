import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# --- [고정 설정 정보] ---
CONFIG = {
    "메디빌더": {"sheet": "HQ_실적", "header": 5, "매출": 14, "영익": 51, "color": "#333333"},
    "온리프": {
        "sheet": "온리프_실적", "header": 6, 
        "전체매출": 25, "전체영익": 52, "병원매출": 77, "병원영익": 116, "법인매출": 121, "법인영익": 155,
        "인건비_병원": 32, "인건비_앤파": 40, "의약품비": 33, "상품매입": 36, "광고비": 42,
        "color": "#1f77b4"
    },
    "르샤인": {
        "sheet": "르샤인_실적", "header": 5,
        "전체매출": 36, "전체영익": 60, "병원매출": 85, "병원영익": 127, "법인매출": 132, "법인영익": 163,
        "인건비_병원": 40, "인건비_앤파": 48, "의약품비": 41, "상품매입": 44, "광고비": 50,
        "color": "#006400"
    },
    "오블리브": {
        "sheet": "오블리브(송도)_실적", "header": 6,
        "전체매출": 34, "전체영익": 58, "병원매출": 83, "병원영익": 125, "법인매출": 130, "법인영익": 163,
        "인건비_병원": 38, "인건비_앤파": 46, "의약품비": 39, "상품매입": 42, "광고비": 48,
        "color": "#8B4513"
    }
}

@st.cache_data
def load_all_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    data_frames, col_maps = {}, {}
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}

    for key, conf in CONFIG.items():
        try:
            df = pd.read_excel(file_name, sheet_name=conf["sheet"], header=None)
            data_frames[key] = df
            h_row = df.iloc[conf["header"]-1]
            c_map = {m_l: i for m_l, m_v in months_dict.items() for i, cell in enumerate(h_row) if str(m_v) in str(cell).replace(".0", "")}
            col_maps[key] = c_map
        except: st.error(f"시트 '{conf['sheet']}' 로드 실패")
    return data_frames, col_maps

def get_val(df, row, col):
    if col is None or pd.isna(col): return 0
    v = pd.to_numeric(df.iloc[row-1, col], errors='coerce')
    return (v if pd.notnull(v) else 0) / 1000000

def display_metrics(months, sales_list, profit_list):
    if len(sales_list) < 1: return
    curr_s, curr_p = sales_list[-1], profit_list[-1]
    curr_r = (curr_p / curr_s * 100) if curr_s != 0 else 0
    
    delta_s, delta_p, delta_r = None, None, None
    if len(sales_list) > 1:
        prev_s, prev_p = sales_list[-2], profit_list[-2]
        prev_r = (prev_p / prev_s * 100) if prev_s != 0 else 0
        delta_s = f"{(curr_s - prev_s)/100:+.1f}억 ({(curr_s/prev_s-1)*100:+.1f}%)" if prev_s != 0 else "N/A"
        delta_p = f"{(curr_p - prev_p)/100:+.1f}억 ({(curr_p/prev_p-1)*100:+.1f}%)" if prev_p != 0 else "N/A"
        delta_r = f"{curr_r - prev_r:+.1f}%p"

    m1, m2, m3 = st.columns(3)
    m1.metric(f"📅 {months[-1]} 매출", f"{curr_s/100:.1f}억", delta_s)
    m2.metric(f"💰 {months[-1]} 영업이익", f"{curr_p/100:.1f}억", delta_p)
    m3.metric(f"📊 {months[-1]} 이익률", f"{curr_r:.1f}%", delta_r)

def draw_chart(title, months, s, p, c):
    st.markdown(f"### {title}")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=p, name="영업이익", marker_color=c, opacity=0.6, text=[f"{v/100:.1f}억" for v in p], textposition="outside"))
    fig.add_trace(go.Scatter(x=months, y=s, name="매출", mode="lines+markers+text", line=dict(color="#FF4B4B", width=3), text=[f"{v/100:.1f}억" for v in s], textposition="top center"))
    fig.update_layout(height=400, margin=dict(l=10,r=10,t=30,b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), yaxis=dict(title="단위: 백만 원"), xaxis=dict(type='category'), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# 주요 비용 차트 함수
def draw_expense_chart(title, months, sales_list, exp_list, exp_label, color):
    # 매출 대비 비율 계산
    ratios = [(e/s*100 if s!=0 else 0) for s, e in zip(sales_list, exp_list)]
    
    fig = go.Figure()
    # 비용 금액 (막대)
    fig.add_trace(go.Bar(x=months, y=exp_list, name=f"{exp_label} 금액", marker_color=color, opacity=0.5, text=[f"{v/100:.1f}억" for v in exp_list], textposition="outside"))
    # 매출 대비 비중 (꺾은선)
    fig.add_trace(go.Scatter(x=months, y=ratios, name=f"{exp_label} 비중(%)", yaxis="y2", mode="lines+markers+text", line=dict(color="orange", width=2), text=[f"{v:.1f}%" for v in ratios], textposition="top right"))
    
    fig.update_layout(
        title=f"🏷️ {title}", height=350, margin=dict(l=10,r=10,t=50,b=10),
        yaxis=dict(title="금액 (백만 원)"),
        yaxis2=dict(title="매출 대비 비중 (%)", overlaying="y", side="right", range=[0, max(ratios)*1.5 if ratios else 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(type='category'), hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 메인 로직 ---
st.sidebar.header("🔍 경영 실적 필터")
selected_mode = st.sidebar.selectbox("🏢 대상 BU 선택", ["연결 실적(통합)", "메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    dfs, maps = load_all_data()
    all_months = list(maps["온리프"].keys())
    start_m, end_m = st.sidebar.select_slider("기간", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed")
    sel_months = all_months[all_months.index(start_m) : all_months.index(end_m) + 1]

    if selected_mode == "연결 실적(통합)":
        st.title("🌐 그룹 연결 실적 현황")
        ts = [get_val(dfs["온리프"], CONFIG["온리프"]["전체매출"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체매출"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체매출"], maps["오블리브"][m]) for m in sel_months]
        tp = [get_val(dfs["온리프"], CONFIG["온리프"]["전체영익"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체영익"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체영익"], maps["오블리브"][m]) + get_val(dfs["메디빌더"], CONFIG["메디빌더"]["영익"], maps["메디빌더"][m]) for m in sel_months]
        display_metrics(sel_months, ts, tp)
        draw_chart("📊 그룹 전체 연결 실적", sel_months, ts, tp, "#E91E63")
        
    else:
        st.title(f"🚀 {selected_mode} 경영 리포트")
        k = "메디빌더" if selected_mode == "메디빌더" else selected_mode.split()[0]
        conf = CONFIG[k]
        
        main_s_row = conf["매출"] if k == "메디빌더" else conf["전체매출"]
        main_p_row = conf["영익"] if k == "메디빌더" else conf["전체영익"]
        sum_s = [get_val(dfs[k], main_s_row, maps[k][m]) for m in sel_months]
        sum_p = [get_val(dfs[k], main_p_row, maps[k][m]) for m in sel_months]
        
        display_metrics(sel_months, sum_s, sum_p)
        draw_chart(f"📊 {k} 실적 추이", sel_months, sum_s, sum_p, conf["color"])

        # --- 주요 비용 분석 섹션 (병원 BU만 표시) ---
        if k in ["온리프", "르샤인", "오블리브"]:
            st.divider()
            st.subheader(f"📑 {k} 핵심 비용 집행 분석")
            st.info("각 비용의 금액(억)과 매출 대비 비중(%)을 분석합니다.")
            
            c1, c2 = st.columns(2)
            # 병원 기준 매출 (비율 계산용)
            h_sales = [get_val(dfs[k], conf["병원매출"], maps[k][m]) for m in sel_months]
            
            with c1:
                labor = [get_val(dfs[k], conf["인건비_병원"], maps[k][m]) for m in sel_months]
                draw_expense_chart("인건비(병원) 분석", sel_months, h_sales, labor, "인건비", "#4B8BBE")
                
                medicine = [get_val(dfs[k], conf["의약품비"], maps[k][m]) for m in sel_months]
                draw_expense_chart("의약품비 분석", sel_months, h_sales, medicine, "의약품비", "#306998")

            with c2:
                purchase = [get_val(dfs[k], conf["상품매입"], maps[k][m]) for m in sel_months]
                draw_expense_chart("상품매입비 분석", sel_months, h_sales, purchase, "상품매입", "#FFE873")
                
                ads = [get_val(dfs[k], conf["광고비"], maps[k][m]) for m in sel_months]
                draw_expense_chart("광고선전비 분석", sel_months, h_sales, ads, "광고비", "#FFD43B")

except Exception as e:
    st.error(f"데이터 처리 중 오류: {e}")
