import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 설정
st.set_page_config(page_title="메디빌더 경영 실적 대시보드", layout="wide")

# --- [컬러 테마 정의] ---
HOSP_ITEM_COLORS = ["#8ECAE6", "#219EBC", "#457B9D", "#A8DADC", "#F1FAEE"]
TOTAL_SPLIT_COLORS = {"그룹 매출": "#BDBDBD", "법인 합산": "#D1C4E9", "병원": "#A8DADC", "앤파트너스": "#F4A261"}

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

# --- [데이터 로드 함수] ---
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

@st.cache_data
def load_raw_data_only():
    file_name = "(2021-2026) 26년 통합 경영관리_3월 마감_260423.xlsx"
    try:
        df = pd.read_excel(file_name, sheet_name="Raw Data_2026", header=0)
        return df
    except:
        return pd.DataFrame()

# --- [유틸리티 함수] ---
def get_val(df, row, col):
    if col is None or pd.isna(col): return 0
    v = pd.to_numeric(df.iloc[row-1, col], errors='coerce')
    return (v if pd.notnull(v) else 0) / 1000000

def generate_headline(months, sales, profits, name, is_item=False):
    if len(months) < 2: return None
    curr_s, prev_s = sales[-1], sales[-2]
    s_diff = (curr_s / prev_s - 1) * 100 if prev_s != 0 else 0
    messages = []
    if s_diff >= 10: messages.append(f"📈 **{name} 성장**: 전월비 **{s_diff:.1f}%** 급증")
    elif s_diff <= -10: messages.append(f"📉 **{name} 하락**: 전월비 **{abs(s_diff):.1f}%** 감소")
    return " | ".join(messages) if messages else None

# --- [시각화 함수] ---
def draw_performance_chart(title, months, sales_dict, profit_list, line_color, use_custom_palette=False):
    st.markdown(f"### {title}") 
    fig = go.Figure()
    for idx, (label, values) in enumerate(sales_dict.items()):
        if label == "Total": continue
        color = HOSP_ITEM_COLORS[idx % len(HOSP_ITEM_COLORS)] if use_custom_palette else TOTAL_SPLIT_COLORS.get(label, "#E0E0E0")
        fig.add_trace(go.Bar(x=months, y=values, name=label, marker_color=color, opacity=0.85))
    
    fig.add_trace(go.Scatter(x=months, y=profit_list, name="영업이익", mode="lines+markers+text", 
                             line=dict(color=line_color, width=3), text=[f"{p:.1f}M" for p in profit_list], textposition="top center"))
    
    fig.update_layout(height=450, barmode='stack', plot_bgcolor="white", hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

def draw_expense_chart(title, months, sales_list, exp_list, exp_label, line_color, bar_color):
    ratios = [(e/s*100 if s!=0 else 0) for s, e in zip(sales_list, exp_list)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=months, y=exp_list, name=f"{exp_label} 금액", marker_color=bar_color, opacity=0.8))
    fig.add_trace(go.Scatter(x=months, y=ratios, name=f"{exp_label} 비중(%)", yaxis="y2", mode="lines+markers", line=dict(color=line_color, width=2)))
    fig.update_layout(title=title, height=350, yaxis2=dict(overlaying="y", side="right", range=[0, max(ratios)*1.5 if ratios else 30]),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

# [수정됨] 의약품비 전표 분석 (시각화 및 표 개선 버전)
def display_vendor_analysis_standalone(raw_df, month, biz_name):
    if raw_df.empty: return
    st.divider()
    st.subheader(f"💊 {biz_name} 의약품비 거래처 상세 분석 (Top 10)")
    try:
        df = raw_df.iloc[:, [0, 1, 2, 3, 16]].copy()
        df.columns = ['Month', 'Amount', 'Biz', 'Category', 'Vendor']
        df = df[(df['Category'] == "03.매출원가-의약품비") & (df['Biz'].str.contains(biz_name, na=False))]
        df['Month'] = pd.to_numeric(df['Month'], errors='coerce')
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
        
        curr_m = int(month.split('.')[1])
        prev_m = curr_m - 1 if curr_m > 1 else 12
        
        curr_df = df[df['Month'] == curr_m].groupby('Vendor')['Amount'].sum().reset_index()
        prev_df = df[df['Month'] == prev_m].groupby('Vendor')['Amount'].sum().reset_index()
        
        merged = pd.merge(curr_df, prev_df, on='Vendor', how='outer', suffixes=('_Curr', '_Prev')).fillna(0)
        merged['Diff'] = merged['Amount_Curr'] - merged['Amount_Prev']
        merged['Growth'] = (merged['Diff'] / merged['Amount_Prev'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        top10 = merged.sort_values(by='Amount_Curr', ascending=False).head(10).reset_index(drop=True)
        # 벤더명 앞에 숫자(순위) 추가
        top10['Vendor'] = [f"{i+1}. {v}" for i, v in enumerate(top10['Vendor'])]
        
        c1, c2 = st.columns([3, 2])
        with c1:
            # 그룹형 막대 그래프로 변경
            fig = go.Figure()
            fig.add_trace(go.Bar(x=top10['Vendor'], y=top10['Amount_Prev']/1000000, name='전월', marker_color='#BDBDBD'))
            fig.add_trace(go.Bar(x=top10['Vendor'], y=top10['Amount_Curr']/1000000, name='당월', marker_color='#219EBC'))
            fig.update_layout(height=450, barmode='group', plot_bgcolor='white', xaxis=dict(tickangle=-45),
                              yaxis=dict(title="금액 (백만 원)"), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("📊 **의약품비 변동 내역 상세 (단위: 백만 원)**")
            display_df = top10.copy()
            # M 제거 및 숫자 포맷팅
            display_df['전월'] = (display_df['Amount_Prev'] / 1000000).map('{:,.1f}'.format)
            display_df['당월'] = (display_df['Amount_Curr'] / 1000000).map('{:,.1f}'.format)
            display_df['차이금액'] = (display_df['Diff'] / 1000000).map('{:+,.1f}'.format)
            display_df['증감율'] = display_df['Growth'].map('{:+.1f}%'.format)
            
            # 표 컬럼 순서 및 우측 정렬 설정
            st.dataframe(
                display_df[['Vendor', '전월', '당월', '차이금액', '증감율']],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "전월": st.column_config.Column(width="small"),
                    "당월": st.column_config.Column(width="small"),
                    "차이금액": st.column_config.Column(width="small"),
                    "증감율": st.column_config.Column(width="small")
                }
            )
            # 숫자를 오른쪽으로 정렬하기 위한 스타일 커스텀
            st.markdown("""<style> div[data-testid="stDataFrame"] td { text-align: right !important; } </style>""", unsafe_allow_html=True)
    except:
        st.info("데이터 분석 중 오류가 발생했거나 해당 월 데이터가 없습니다.")

# --- [메인 실행부] ---
st.sidebar.header("🔍 경영 실적 필터")
selected_mode = st.sidebar.selectbox("🏢 대상 BU 선택", ["연결 실적(통합)", "메디빌더", "온리프 BU", "르샤인 BU", "오블리브 BU"])

try:
    dfs, maps = load_all_data()
    all_months = list(maps["온리프"].keys())
    start_m, end_m = st.sidebar.select_slider("기간", options=all_months, value=(all_months[0], all_months[-1]))
    sel_months = all_months[all_months.index(start_m) : all_months.index(end_m) + 1]

    if selected_mode == "연결 실적(통합)":
        st.title("🌐 그룹 연결 실적 현황")
        ts = [get_val(dfs["온리프"], CONFIG["온리프"]["전체매출"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체매출"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체매출"], maps["오블리브"][m]) for m in sel_months]
        tp = [get_val(dfs["온리프"], CONFIG["온리프"]["전체영익"], maps["온리프"][m]) + get_val(dfs["르샤인"], CONFIG["르샤인"]["전체영익"], maps["르샤인"][m]) + get_val(dfs["오블리브"], CONFIG["오블리브"]["전체영익"], maps["오블리브"][m]) + get_val(dfs["메디빌더"], CONFIG["메디빌더"]["영익"], maps["메디빌더"][m]) for m in sel_months]
        draw_performance_chart("📊 전체 연결 실적", sel_months, {"Total": ts, "그룹 매출": ts}, tp, "#1D3557")
    else:
        st.title(f"🚀 {selected_mode} 경영 리포트")
        k = "메디빌더" if selected_mode == "메디빌더" else selected_mode.split()[0]
        conf = CONFIG[k]
        sum_s = [get_val(dfs[k], (conf["매출"] if k=="메디빌더" else conf["전체매출"]), maps[k][m]) for m in sel_months]
        sum_p = [get_val(dfs[k], (conf["영익"] if k=="메디빌더" else conf["전체영익"]), maps[k][m]) for m in sel_months]
        
        draw_performance_chart(f"📊 {k} 전체 실적", sel_months, {"Total": sum_s, "매출": sum_s}, sum_p, conf["color"])
        
        if k in ["온리프", "르샤인", "오블리브"]:
            st.divider()
            h_total_s = [get_val(dfs[k], conf["병원매출"], maps[k][m]) for m in sel_months]
            h_profit = [get_val(dfs[k], conf["병원영익"], maps[k][m]) for m in sel_months]
            draw_performance_chart(f"🏥 {k} 의원 실적", sel_months, {"Total": h_total_s, "병원 매출": h_total_s}, h_profit, conf["color"])
            
            st.divider(); st.subheader(f"📑 {k} 핵심 비용 분석")
            c1, c2 = st.columns(2)
            with c1:
                draw_expense_chart("인건비(병원) 분석", sel_months, h_total_s, [get_val(dfs[k], conf["인건비_병원"], maps[k][m]) for m in sel_months], "인건비", conf["color"], "#A8DADC")
                draw_expense_chart("의약품비 분석", sel_months, h_total_s, [get_val(dfs[k], conf["의약품비"], maps[k][m]) for m in sel_months], "의약품비", conf["color"], "#457B9D")
            with c2:
                draw_expense_chart("광고선전비 분석", sel_months, h_total_s, [get_val(dfs[k], conf["광고비"], maps[k][m]) for m in sel_months], "광고비", conf["color"], "#F1FAEE")
            
            # 최하단 전표 데이터 분석 섹션
            raw_data = load_raw_data_only()
            display_vendor_analysis_standalone(raw_data, end_m, k)

except Exception as e:
    st.error(f"데이터 처리 오류: {e}")
