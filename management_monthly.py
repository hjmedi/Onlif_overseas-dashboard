import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# --- [컬러 테마 정의] ---
HOSP_ITEM_COLORS = ["#8ECAE6", "#219EBC", "#457B9D", "#A8DADC", "#F1FAEE"]
TOTAL_SPLIT_COLORS = {"그룹 매출": "#BDBDBD", "법인 합산": "#D1C4E9", "병원": "#A8DADC", "앤파트너스": "#F4A261"}

CONFIG = {
    "메디빌더": {"sheet": "HQ_실적", "header": 5, "매출": 14, "영익": 51, "color": "#333333", "biz_name": "메디빌더"},
    "온리프": {
        "sheet": "온리프_실적", "header": 6, "전체매출": 25, "전체영익": 52, "병원매출": 77, "병원영익": 116, "법인매출": 121, "법인영익": 155,
        "인건비_병원": 32, "인건비_앤파": 40, "의약품비": 33, "상품매입": 36, "광고비": 42, "color": "#1f77b4", "hosp_items": {}, "biz_name": "온리프", "anpa_row": 40
    },
    "르샤인": {
        "sheet": "르샤인_실적", "header": 5, "전체매출": 36, "전체영익": 60, "병원매출": 85, "병원영익": 127, "법인매출": 132, "법인영익": 163,
        "인건비_병원": 40, "인건비_앤파": 48, "의약품비": 41, "상품매입": 44, "광고비": 50, "color": "#006400",
        "hosp_items": {"피부체형": 87, "문제성발톱": 88, "재활의학": 89, "공단매출": 91}, "anpa_row": 38, "biz_name": "르샤인"
    },
    "오블리브": {
        "sheet": "오블리브(송도)_실적", "header": 6, "전체매출": 34, "전체영익": 58, "병원매출": 83, "병원영익": 125, "법인매출": 130, "법인영익": 163,
        "인건비_병원": 38, "인건비_앤파": 46, "의약품비": 39, "상품매입": 42, "광고비": 48, "color": "#8B4513",
        "hosp_items": {"피부체형": 85, "문제성발톱": 86, "재활의학": 87, "공단매출": 88}, "anpa_row": 36, "biz_name": "오블리브"
    }
}

# --- [공통 데이터 로드] ---
@st.cache_data
def load_all_data():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    raw_dfs = pd.read_excel(file_name, sheet_name=None, header=None)
    try:
        # 1행 헤더 (D열 계정항목 필터링을 위해 로드)
        raw_data_2026 = pd.read_excel(file_name, sheet_name="Raw Data_2026", header=0)
    except:
        raw_data_2026 = pd.DataFrame()
    
    months_dict = {"25.01": "2501", "25.02": "2502", "25.03": "2503", "25.04": "2504", "25.05": "2505", "25.06": "2506", 
                   "25.07": "2507", "25.08": "2508", "25.09": "2509", "25.10": "2510", "25.11": "2511", "25.12": "2512", 
                   "26.01": "2601", "26.02": "2602"}
    col_maps = {}
    for key, conf in CONFIG.items():
        h_row = raw_dfs[conf["sheet"]].iloc[conf["header"]-1]
        col_maps[key] = {m_l: i for m_l, m_v in months_dict.items() for i, cell in enumerate(h_row) if str(m_v) in str(cell).replace(".0", "")}
    
    return raw_dfs, raw_data_2026, col_maps

def get_val(df, row, col):
    if col is None or pd.isna(col): return 0
    v = pd.to_numeric(df.iloc[row-1, col], errors='coerce')
    return (v if pd.notnull(v) else 0) / 1000000

# --- [차트 및 지표 함수] ---
def draw_performance_chart(title, months, sales_dict, profit_list, line_color, use_custom_palette=False):
    st.markdown(f"### {title}")
    if use_custom_palette:
        item_issues = generate_item_headlines(months, sales_dict)
        if item_issues:
            with st.expander("📌 의원 센터별 주요 변동 이슈 확인"):
                for issue in item_issues: st.write(issue)

    fig = go.Figure()
    for idx, (label, values) in enumerate(sales_dict.items()):
        if label == "Total": continue
        color = HOSP_ITEM_COLORS[idx % len(HOSP_ITEM_COLORS)] if use_custom_palette else TOTAL_SPLIT_COLORS.get(label, "#E0E0E0")
        fig.add_trace(go.Bar(x=months, y=values, name=label, marker_color=color, marker_line_width=0, opacity=0.85))

    total_sales = sales_dict.get("Total", [0]*len(months))
    profit_labels = [f"{p/100:.1f}억<br>({(p/s*100) if s!=0 else 0:.1f}%)" for s, p in zip(total_sales, profit_list)]
    fig.add_trace(go.Scatter(x=months, y=profit_list, name="영업이익", mode="lines+markers+text", 
                             line=dict(color=line_color, width=3.5), marker=dict(size=8, symbol="circle", line=dict(color='white', width=2)),
                             text=profit_labels, textposition="top center", textfont=dict(size=11, color=line_color)))
    if "Total" in sales_dict:
        fig.add_trace(go.Scatter(x=months, y=sales_dict["Total"], mode="text", text=[f"{v/100:.1f}억" for v in sales_dict["Total"]], 
                                 textposition="top center", showlegend=False, hoverinfo='none', textfont=dict(color="#444444", size=11)))
    fig.update_layout(height=480, margin=dict(l=10,r=10,t=40,b=10), barmode='stack', plot_bgcolor="white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

def draw_expense_chart(title, months, sales_list, exp_list, exp_label, line_color, bar_color):
    ratios = [(e/s*100 if s!=0 else 0) for s, e in zip(sales_list, exp_list)]
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=exp_list, name=f"{exp_label} 금액", marker_color=bar_color, opacity=0.8, marker_line_width=1, text=[f"{v/100:.1f}억" for v in exp_list], textposition="outside"))
    fig.add_trace(go.Scatter(x=months, y=ratios, name=f"{exp_label} 비중(%)", yaxis="y2", mode="lines+markers+text", line=dict(color=line_color, width=2.5), text=[f"{v:.1f}%" for v in ratios], textposition="top center"))
    fig.add_hline(y=avg_ratio, line_dash="dot", line_color="#D32F2F", yref="y2", annotation_text=f"평균 {avg_ratio:.1f}%", annotation_position="top left")
    fig.update_layout(title=dict(text=f"<b>{title}</b>", font=dict(size=18)), height=380, margin=dict(l=10,r=10,t=60,b=10), yaxis=dict(title="금액 (백만 원)", showgrid=False), yaxis2=dict(title="비중 (%)", overlaying="y", side="right", range=[0, max(ratios)*1.6 if ratios else 30], showgrid=False), plot_bgcolor="white", hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

# --- [신규: 거래처별 의약품비 정교화 필터링] ---
def display_vendor_analysis(raw_df, month, biz_name):
    st.divider()
    st.subheader(f"💊 {biz_name} 의약품비 거래처 상세 분석 (Top 10)")
    
    try:
        # 컬럼 추출: A(월구분), B(금액), C(사업자구분), D(계정항목), Q(거래처명)
        # 엑셀 상의 위치: A=0, B=1, C=2, D=3, Q=16
        df = raw_df.iloc[:, [0, 1, 2, 3, 16]]
        df.columns = ['Month', 'Amount', 'Biz', 'Category', 'Vendor']
        
        # 1. 의약품비 전표만 필터링 (D열 기준)
        target_category = "03.매출원가-의약품비"
        df = df[df['Category'] == target_category]
        
        # 2. 데이터 타입 정리
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        
        curr_m = int(month.split('.')[1])
        prev_m = curr_m - 1 if curr_m > 1 else 12
        
        # 3. 사업자 필터링 및 당월/전월 집계
        biz_df = df[df['Biz'].str.contains(biz_name, na=False)]
        curr_df = biz_df[biz_df['Month'] == curr_m].groupby('Vendor')['Amount'].sum().reset_index()
        prev_df = biz_df[biz_df['Month'] == prev_m].groupby('Vendor')['Amount'].sum().reset_index()
        
        # 4. 비교 데이터 생성
        merged = pd.merge(curr_df, prev_df, on='Vendor', how='outer', suffixes=('_Curr', '_Prev')).fillna(0)
        merged['Diff'] = merged['Amount_Curr'] - merged['Amount_Prev']
        merged['Growth'] = (merged['Diff'] / merged['Amount_Prev'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        top10 = merged.sort_values(by='Amount_Curr', ascending=False).head(10)
        
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=top10['Vendor'], y=top10['Amount_Curr']/1000000, name='당월 금액', marker_color='#219EBC'))
            fig.add_trace(go.Scatter(x=top10['Vendor'], y=top10['Amount_Prev']/1000000, name='전월 금액', mode='markers', marker=dict(size=12, color='#FB8500', symbol='diamond')))
            fig.update_layout(height=400, title="단위: 백만원 (다이아몬드는 전월 실적)", barmode='group', plot_bgcolor='white', xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("📊 **의약품비 변동 상세 (Top 10)**")
            display_df = top10.copy()
            display_df['Amount_Curr'] = display_df['Amount_Curr'].apply(lambda x: f"{x/1000000:.1f}M")
            display_df['Diff'] = display_df['Diff'].apply(lambda x: f"{x/1000000:+.1f}M")
            display_df['Growth'] = display_df['Growth'].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(display_df[['Vendor', 'Amount_Curr', 'Diff', 'Growth']], hide_index=True, use_container_width=True)
            
    except Exception as e:
        st.info(f"{biz_name}의 해당 월 '03.매출원가-의약품비' 전표가 없습니다.")

# --- [기타 헬퍼 함수] ---
def generate_headline(months, sales, profits, name):
    if len(months) < 2: return None
    s_diff = (sales[-1] / sales[-2] - 1) * 100 if sales[-2] != 0 else 0
    curr_r = (profits[-1] / sales[-1] * 100) if sales[-1] != 0 else 0
    prev_r = (profits[-2] / sales[-2] * 100) if sales[-2] != 0 else 0
    r_diff = curr_r - prev_r
    msg = []
    if s_diff >= 10: msg.append(f"📈 **{name} 성장**: 전월비 **{s_diff:.1f}%** 상승")
    elif s_diff <= -10: msg.append(f"📉 **{name} 하락**: 전월비 **{abs(s_diff):.1f}%** 감소")
    if r_diff >= 5: msg.append(f"✨ **수익 최적화**: 이익률 **{r_diff:.1f}%p** 개선")
    return " | ".join(msg) if msg else None

def generate_item_headlines(months, item_dict):
    if len(months) < 2: return []
    issues = []
    for name, values in item_dict.items():
        if name == "Total": continue
        diff = (values[-1] / values[-2] - 1) * 100 if values[-2] > 0 else 0
        if diff >= 15: issues.append(f"🔥 **{name}** 항목 **{diff:.1f}%** 급증")
    return issues

def display_metrics(months, sales_list, profit_list):
    if len(sales_list) < 1: return
    curr_s, prev_s = sales_list[-1], sales_list[-2] if len(sales_list)>1 else sales_list[-1]
    curr_p = profit_list[-1]
    m1, m2, m3 = st.columns(3)
    m1.metric(f"📅 {months[-1]} 매출", f"{curr_s/100:.1f}억", f"{(curr_s-prev_s)/100:+.1f}억")
    m2.metric(f"💰 {months[-1]} 영업이익", f"{curr_p/100:.1f}억")
    m3.metric(f"📊 {months[-1]} 이익률", f"{(curr_p/curr_s*100):.1f}%")

# --- 메인 실행 ---
raw_dfs, raw_data_2026, col_maps = load_all_data()
st.sidebar.header("🔍 경영 실적 필터")
selected_mode = st.sidebar.selectbox("🏢 대상 BU 선택", ["연결 실적(통합)", "메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"])
all_months = list(col_maps["온리프"].keys())
start_m, end_m = st.sidebar.select_slider("기간", options=all_months, value=(all_months[0], all_months[-1]), label_visibility="collapsed")
sel_months = all_months[all_months.index(start_m) : all_months.index(end_m) + 1]

if selected_mode == "연결 실적(통합)":
    st.title("🌐 그룹 연결 실적 현황")
    ts = [get_val(raw_dfs["온리프_실적"], 25, col_maps["온리프"][m]) + get_val(raw_dfs["르샤인_실적"], 36, col_maps["르샤인"][m]) + get_val(raw_dfs["오블리브(송도)_실적"], 34, col_maps["오블리브"][m]) for m in sel_months]
    tp = [get_val(raw_dfs["온리프_실적"], 52, col_maps["온리프"][m]) + get_val(raw_dfs["르샤인_실적"], 60, col_maps["르샤인"][m]) + get_val(raw_dfs["오블리브(송도)_실적"], 58, col_maps["오블리브"][m]) + get_val(raw_dfs["HQ_실적"], 51, col_maps["메디빌더"][m]) for m in sel_months]
    h_line = generate_headline(sel_months, ts, tp, "그룹 전체")
    if h_line: st.success(h_line)
    display_metrics(sel_months, ts, tp); draw_performance_chart("📊 전체 연결", sel_months, {"Total": ts, "그룹 매출": ts}, tp, "#1D3557")
    st.divider()
    cs = [get_val(raw_dfs["HQ_실적"], 14, col_maps["메디빌더"][m]) + get_val(raw_dfs["온리프_실적"], 121, col_maps["온리프"][m]) + get_val(raw_dfs["르샤인_실적"], 132, col_maps["르샤인"][m]) + get_val(raw_dfs["오블리브(송도)_실적"], 130, col_maps["오블리브"][m]) for m in sel_months]
    cp = [get_val(raw_dfs["온리프_실적"], 155, col_maps["온리프"][m]) + get_val(raw_dfs["르샤인_실적"], 163, col_maps["르샤인"][m]) + get_val(raw_dfs["오블리브(송도)_실적"], 163, col_maps["오블리브"][m]) + get_val(raw_dfs["HQ_실적"], 51, col_maps["메디빌더"][m]) for m in sel_months]
    display_metrics(sel_months, cs, cp); draw_performance_chart("🏢 법인 연결(HQ+파트너스)", sel_months, {"Total": cs, "법인 합산": cs}, cp, "#6D597A")
else:
    k = "메디빌더" if selected_mode == "메디빌더" else selected_mode.split()[0]
    conf = CONFIG[k]
    st.title(f"🚀 {selected_mode} 경영 리포트")
    sum_s = [get_val(raw_dfs[conf["sheet"]], (conf["매출"] if k=="메디빌더" else conf["전체매출"]), col_maps[k][m]) for m in sel_months]
    sum_p = [get_val(raw_dfs[conf["sheet"]], (conf["영익"] if k=="메디빌더" else conf["전체영익"]), col_maps[k][m]) for m in sel_months]
    h_line = generate_headline(sel_months, sum_s, sum_p, k)
    if h_line: st.info(h_line)
    display_metrics(sel_months, sum_s, sum_p)
    if k in ["르샤인", "오블리브"]:
        anpa_s = [get_val(raw_dfs[conf["sheet"]], conf["anpa_row"], col_maps[k][m]) for m in sel_months]
        draw_performance_chart(f"📊 {k} 전체 실적 (병원 + 앤파트너스)", sel_months, {"Total": sum_s, "병원": [s-a for s, a in zip(sum_s, anpa_s)], "앤파트너스": anpa_s}, sum_p, conf["color"])
    else: draw_performance_chart(f"📊 {k} 전체 실적 추이", sel_months, {"Total": sum_s, "전체 매출": sum_s}, sum_p, conf["color"])
    if k in ["온리프", "르샤인", "오블리브"]:
        st.divider()
        h_s, h_p = [get_val(raw_dfs[conf["sheet"]], conf["병원매출"], col_maps[k][m]) for m in sel_months], [get_val(raw_dfs[conf["sheet"]], conf["병원영익"], col_maps[k][m]) for m in sel_months]
        if conf.get("hosp_items"):
            h_dict = {"Total": h_s}
            for it_n, it_r in conf["hosp_items"].items(): h_dict[it_n] = [get_val(raw_dfs[conf["sheet"]], it_r, col_maps[k][m]) for m in sel_months]
            draw_performance_chart(f"🏥 {k} 의원 센터별 상세 실적", sel_months, h_dict, h_p, conf["color"], True)
        else: draw_performance_chart(f"🏥 {k} 의원 실적", sel_months, {"Total": h_s, "병원 매출": h_s}, h_p, conf["color"])
        p_s, p_p = [get_val(raw_dfs[conf["sheet"]], conf["법인매출"], col_maps[k][m]) for m in sel_months], [get_val(raw_dfs[conf["sheet"]], conf["법인영익"], col_maps[k][m]) for m in sel_months]
        draw_performance_chart(f"🤝 {k} 앤파트너스 실적", sel_months, {"Total": p_s, "앤파트너스 매출": p_s}, p_p, conf["color"])
        st.divider(); st.subheader(f"📑 {k} 5대 핵심 비용 분석")
        c1, c2 = st.columns(2)
        with c1:
            draw_expense_chart("① 인건비(병원) 분석", sel_months, h_s, [get_val(raw_dfs[conf["sheet"]], conf["인건비_병원"], col_maps[k][m]) for m in sel_months], "인건비(병)", conf["color"], "#A8DADC")
            draw_expense_chart("③ 의약품비 분석", sel_months, h_s, [get_val(raw_dfs[conf["sheet"]], conf["의약품비"], col_maps[k][m]) for m in sel_months], "의약품비", conf["color"], "#457B9D")
            draw_expense_chart("⑤ 광고선전비 분석", sel_months, h_s, [get_val(raw_dfs[conf["sheet"]], conf["광고비"], col_maps[k][m]) for m in sel_months], "광고비", conf["color"], "#F1FAEE")
        with c2:
            draw_expense_chart("② 인건비(앤파) 분석", sel_months, p_s, [get_val(raw_dfs[conf["sheet"]], conf["인건비_앤파"], col_maps[k][m]) for m in sel_months], "인건비(앤파)", conf["color"], "#A8DADC")
            draw_expense_chart("④ 상품매입 분석", sel_months, h_s, [get_val(raw_dfs[conf["sheet"]], conf["상품매입"], col_maps[k][m]) for m in sel_months], "상품매입", conf["color"], "#F4A261")
        display_vendor_analysis(raw_data_2026, end_m, conf["biz_name"])
