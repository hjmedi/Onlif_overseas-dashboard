import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# --- [컬러 테마 정의] ---
HOSP_ITEM_COLORS = ["#8ECAE6", "#219EBC", "#457B9D", "#A8DADC", "#F1FAEE"]
# 연결 실적 및 BU 전체 실적용 색상
TOTAL_SPLIT_COLORS = {
    "그룹 매출": "#BDBDBD", 
    "법인 합산": "#D1C4E9", 
    "병원": "#A8DADC", 
    "앤파트너스": "#F4A261"
}

CONFIG = {
    "메디빌더": {"sheet": "HQ_실적", "header": 5, "매출": 14, "영익": 51, "color": "#333333"},
    "온리프": {
        "sheet": "온리프_실적", "header": 6, 
        "전체매출": 25, "전체영익": 52, "병원매출": 77, "병원영익": 116, "법인매출": 121, "법인영익": 155,
        "인건비_병원": 32, "인건비_앤파": 40, "의약품비": 33, "상품매입": 36, "광고비": 42,
        "color": "#1f77b4", "hosp_items": {} 
    },
    "르샤인": {
        "sheet": "르샤인_실적", "header": 5,
        "전체매출": 36, "전체영익": 60, "병원매출": 85, "병원영익": 127, "법인매출": 132, "법인영익": 163,
        "인건비_병원": 40, "인건비_앤파": 48, "의약품비": 41, "상품매입": 44, "광고비": 50,
        "color": "#006400",
        "hosp_items": {"피부체형": 87, "문제성발톱": 88, "재활의학": 89, "공단매출": 91},
        "anpa_row": 38 
    },
    "오블리브": {
        "sheet": "오블리브(송도)_실적", "header": 6,
        "전체매출": 34, "전체영익": 58, "병원매출": 83, "병원영익": 125, "법인매출": 130, "법인영익": 163,
        "인건비_병원": 38, "인건비_앤파": 46, "의약품비": 39, "상품매입": 42, "광고비": 48,
        "color": "#8B4513",
        "hosp_items": {"피부체형": 85, "문제성발톱": 86, "재활의학": 87, "공단매출": 88},
        "anpa_row": 36
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

def draw_performance_chart(title, months, sales_dict, profit_list, line_color, use_custom_palette=False):
    st.markdown(f"### {title}")
    fig = go.Figure()

    for idx, (label, values) in enumerate(sales_dict.items()):
        if label == "Total": continue
        if use_custom_palette:
            color = HOSP_ITEM_COLORS[idx % len(HOSP_ITEM_COLORS)]
        else:
            color = TOTAL_SPLIT_COLORS.get(label, "#E0E0E0")
            
        fig.add_trace(go.Bar(x=months, y=values, name=label, marker_color=color, marker_line_width=0, opacity=0.85))

    fig.add_trace(go.Scatter(
        x=months, y=profit_list, name="영업이익", mode="lines+markers+text", 
        line=dict(color=line_color, width=3.5), 
        marker=dict(size=8, symbol="circle", line=dict(color='white', width=2)),
        text=[f"{v/100:.1f}억" for v in profit_list], textposition="top center"
    ))
    
    if "Total" in sales_dict:
        fig.add_trace(go.Scatter(
            x=months, y=sales_dict["Total"], mode="text", text=[f"{v/100:.1f}억" for v in sales_dict["Total"]], 
            textposition="top center", showlegend=False, hoverinfo='none',
            textfont=dict(color="#444444", size=11)
        ))

    fig.update_layout(
        height=450, margin=dict(l=10,r=10,t=40,b=10),
        barmode='stack', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="금액 (백만 원)", gridcolor="#F5F5F5"), xaxis=dict(type='category', showgrid=False),
        plot_bgcolor="white", hovermode="x unified"
    )
    fig.add_hline(y=0, line_dash="dash", line_color="#DDDDDD")
    st.plotly_chart(fig, use_container_width=True)

def draw_expense_chart(title, months, sales_list, exp_list, exp_label, line_color, bar_color):
    ratios = [(e/s*100 if s!=0 else 0) for s, e in zip(sales_list, exp_list)]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=months, y=exp_list, name=f"{exp_label} 금액", 
        marker_color=bar_color, opacity=0.8, # 가독성 개선 위해 진하게 수정
        marker_line_color=bar_color, marker_line_width=1,
        text=[f"{v/100:.1f}억" for v in exp_list], textposition="outside"
    ))
    fig.add_trace(go.Scatter(x=months, y=ratios, name=f"{exp_label} 비중(%)", yaxis="y2", mode="lines+markers+text", line=dict(color=line_color, width=2.5), text=[f"{v:.1f}%" for v in ratios], textposition="top center"))
    fig.add_hline(y=avg_ratio, line_dash="dot", line_color="#D32F2F", yref="y2", annotation_text=f"평균 {avg_ratio:.1f}%", annotation_position="top left")
    fig.update_layout(title=dict(text=f"<b>{title}</b>", font=dict(size=18)), height=380, margin=dict(l=10,r=10,t=60,b=10), yaxis=dict(title="금액 (백만 원)", showgrid=False), yaxis2=dict(title="비중 (%)", overlaying="y", side="right", range=[0, max(ratios)*1.6 if ratios else 30], showgrid=False), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), xaxis=dict(type='category'), plot_bgcolor="white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

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
    m1.metric(f"📅 {months[-1]} 매출", f"{curr_s/100:.1f}억", delta_s); m2.metric(f"💰 {months[-1]} 영업이익", f"{curr_p/100:.1f}억", delta_p); m3.metric(f"📊 {months[-1]} 이익률", f"{curr_r:.1f}%", delta_r)

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
        # 1. 전체 연결
        ts = [get_val(dfs["온리프"], CONFIG["온리프"]["전체매출"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체매출"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체매출"], maps["오블리브"][m]) for m in sel_months]
        tp = [get_val(dfs["온리프"], CONFIG["온리프"]["전체영익"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체영익"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체영익"], maps["오블리브"][m]) + get_val(dfs["메디빌더"], CONFIG["메디빌더"]["영익"], maps["메디빌더"][m]) for m in sel_months]
        display_metrics(sel_months, ts, tp)
        draw_performance_chart("📊 그룹 전체 연결 실적", sel_months, {"Total": ts, "그룹 매출": ts}, tp, "#1D3557")
        st.divider()
        # 2. 법인 연결 (복구 완료)
        cs = [get_val(dfs["메디빌더"], CONFIG["메디빌더"]["매출"], maps["메디빌더"][m]) + get_val(dfs["온리프"], CONFIG["온리프"]["법인매출"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["법인매출"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["법인매출"], maps["오블리브"][m]) for m in sel_months]
        cp = [get_val(dfs["온리프"], CONFIG["온리프"]["법인영익"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["법인영익"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["법인영익"], maps["오블리브"][m]) + get_val(dfs["메디빌더"], CONFIG["메디빌더"]["영익"], maps["메디빌더"][m]) for m in sel_months]
        st.subheader("🏢 법인 합산 실적 (HQ + 앤파트너스)")
        display_metrics(sel_months, cs, cp)
        draw_performance_chart("🏢 법인 연결 실적 추이", sel_months, {"Total": cs, "법인 합산": cs}, cp, "#6D597A")
        
    else:
        st.title(f"🚀 {selected_mode} 경영 리포트")
        k = "메디빌더" if selected_mode == "메디빌더" else selected_mode.split()[0]
        conf = CONFIG[k]
        main_s_row, main_p_row = (conf["매출"], conf["영익"]) if k == "메디빌더" else (conf["전체매출"], conf["전체영익"])
        sum_s = [get_val(dfs[k], main_s_row, maps[k][m]) for m in sel_months]
        sum_p = [get_val(dfs[k], main_p_row, maps[k][m]) for m in sel_months]
        display_metrics(sel_months, sum_s, sum_p)

        # BU 실적 (병원 vs 앤파 2분할 복구)
        if k in ["르샤인", "오블리브"]:
            anpa_s = [get_val(dfs[k], conf["anpa_row"], maps[k][m]) for m in sel_months]
            hosp_total_s = [s - a for s, a in zip(sum_s, anpa_s)]
            draw_performance_chart(f"📊 {k} 전체 실적 (병원 vs 앤파트너스)", sel_months, {"Total": sum_s, "병원": hosp_total_s, "앤파트너스": anpa_s}, sum_p, conf["color"])
        else:
            draw_performance_chart(f"📊 {k} 전체 실적 추이", sel_months, {"Total": sum_s, "전체 매출": sum_s}, sum_p, conf["color"])

        if k in ["온리프", "르샤인", "오블리브"]:
            st.divider()
            h_total_s = [get_val(dfs[k], conf["병원매출"], maps[k][m]) for m in sel_months]
            h_profit = [get_val(dfs[k], conf["병원영익"], maps[k][m]) for m in sel_months]
            
            # 병원 상세 (센터별 4대 실적)
            if conf.get("hosp_items"):
                h_sales_dict = {"Total": h_total_s}
                for item_name, item_row in conf["hosp_items"].items():
                    h_sales_dict[item_name] = [get_val(dfs[k], item_row, maps[k][m]) for m in sel_months]
                draw_performance_chart(f"🏥 {k} 의원 센터별 상세 실적", sel_months, h_sales_dict, h_profit, conf["color"], use_custom_palette=True)
            else:
                draw_performance_chart(f"🏥 {k} 의원 실적", sel_months, {"Total": h_total_s, "병원 매출": h_total_s}, h_profit, conf["color"])

            p_sales = [get_val(dfs[k], conf["법인매출"], maps[k][m]) for m in sel_months]
            p_profit = [get_val(dfs[k], conf["법인영익"], maps[k][m]) for m in sel_months]
            draw_performance_chart(f"🤝 {k} 앤파트너스 실적", sel_months, {"Total": p_sales, "앤파트너스 매출": p_sales}, p_profit, conf["color"])

            st.divider(); st.subheader(f"📑 {k} 5대 핵심 비용 분석")
            c1, c2 = st.columns(2)
            with c1:
                draw_expense_chart("① 인건비(병원) 분석", sel_months, h_total_s, [get_val(dfs[k], conf["인건비_병원"], maps[k][m]) for m in sel_months], "인건비(병)", conf["color"], "#A8DADC")
                draw_expense_chart("③ 의약품비 분석", sel_months, h_total_s, [get_val(dfs[k], conf["의약품비"], maps[k][m]) for m in sel_months], "의약품비", conf["color"], "#457B9D")
                draw_expense_chart("⑤ 광고선전비 분석", sel_months, h_total_s, [get_val(dfs[k], conf["광고비"], maps[k][m]) for m in sel_months], "광고비", conf["color"], "#F1FAEE")
            with c2:
                draw_expense_chart("② 인건비(앤파) 분석", sel_months, p_sales, [get_val(dfs[k], conf["인건비_앤파"], maps[k][m]) for m in sel_months], "인건비(앤파)", conf["color"], "#A8DADC")
                draw_expense_chart("④ 상품매입 분석", sel_months, h_total_s, [get_val(dfs[k], conf["상품매입"], maps[k][m]) for m in sel_months], "상품매입", conf["color"], "#F4A261")

except Exception as e:
    st.error(f"데이터 처리 중 오류: {e}")
