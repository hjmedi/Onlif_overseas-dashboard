import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 데이터 주소 및 수수료율 설정
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = {
    "레이블": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "The SC": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "천수현 대표": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "앤티스": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv",
    "크리에이트립": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2000088021&single=true&output=csv"
}

# 에이전트별 수수료율 정의 (기본값 15%, 크리에이트립 11%)
COMMISSION_RATES = {
    "레이블": 0.15,
    "The SC": 0.15,
    "천수현 대표": 0.15,
    "앤티스": 0.15, 
    "크리에이트립": 0.11
}

# 🌍 권역 매핑 함수
def get_region(nation):
    nation = str(nation).strip()
    if nation in ['중국', '대만', '홍콩', '마카오', 'China', 'Taiwan', 'Hong Kong']: return '중화권'
    elif nation in ['일본', 'Japan']: return '일본'
    elif nation in ['태국', '베트남', '싱가포르', '필리핀', '말레이시아', '인도네시아', '미얀마', '캄보디아', '라오스']: return '동남아'
    elif nation in ['미국', '캐나다', 'USA', 'Canada', 'United States']: return '북미'
    elif nation in ['영국', '프랑스', '독일', '이탈리아', '스페인', '러시아', '네덜란드']: return '유럽'
    else: return '기타'

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

# 🔥 축 단위 '백' 자동 생성 함수
def get_dynamic_ticks(max_val):
    if pd.isna(max_val) or max_val == 0: return [0], ["0"]
    if max_val >= 100000000: step = 50000000      # 1억 이상이면 5천만 단위
    elif max_val >= 50000000: step = 20000000    # 5천만 이상이면 2천만 단위
    elif max_val >= 20000000: step = 10000000    # 2천만 이상이면 1천만 단위
    elif max_val >= 10000000: step = 5000000     # 1천만 이상이면 5백만 단위
    else: step = 2000000                         # 그 이하는 2백만 단위
    
    vals = list(range(0, int(max_val) + step*2, step))
    txts = [f"{v/1000000:g}백" if v != 0 else "0" for v in vals]
    return vals, txts

@st.cache_data(ttl=30)
def load_all_data():
    res_m = requests.get(URL_MAIN)
    df_m_raw = pd.read_csv(StringIO(res_m.content.decode('utf-8-sig')), header=None)
    h_idx = 0
    for i in range(len(df_m_raw)):
        if '이름' in "".join(df_m_raw.iloc[i].fillna('').astype(str)):
            h_idx = i; break
    df_m = df_m_raw.copy()
    df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna('미지정')]
    df_m = df_m.drop(range(h_idx + 1)).reset_index(drop=True)
    div_col = [c for c in df_m.columns if '구분' in c or '해외' in c]
    if div_col:
        df_m = df_m[df_m[div_col[0]].astype(str).str.contains('해외', na=False)]
    amt_col = [c for c in df_m.columns if '수납액' in c and 'CRM' in c]
    if not amt_col: amt_col = [c for c in df_m.columns if '수납액' in c]
    df_m['매출액_숫자'] = df_m[amt_col[0]].apply(to_numeric) / 1.1 if amt_col else 0
    df_m['권역'] = df_m['국적'].apply(get_region)
    
    comm_list = []
    for name, url in COMMISSION_URLS.items():
        try:
            r = requests.get(url)
            temp = pd.read_csv(StringIO(r.content.decode('utf-8-sig')))
            df_c = pd.DataFrame({
                '에이전트': name,
                '국적': temp.iloc[:, 3],
                '날짜': temp.iloc[:, 4],
                '매출액': temp.iloc[:, 8].apply(to_numeric)
            })
            if name == "크리에이트립":
                df_c = df_c[df_c['국적'].astype(str).str.contains('중국', na=False)]
            comm_list.append(df_c)
        except: continue
        
    df_comm_total = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()
    if not df_comm_total.empty:
        df_comm_total['수수료율'] = df_comm_total['에이전트'].map(COMMISSION_RATES).fillna(0.15)
        df_comm_total['지급수수료'] = df_comm_total['매출액'] * df_comm_total['수수료율']
        df_comm_total['실매출액'] = df_comm_total['매출액'] - df_comm_total['지급수수료']
    return df_m, df_comm_total

df_main_raw, df_comm_raw = load_all_data()

def format_date(df, col):
    target_col = [c for c in df.columns if col in c]
    if target_col:
        df['날짜형'] = pd.to_datetime(df[target_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형'])
        df['매출월'] = df['날짜형'].dt.strftime('%y년 %m월')
        df['월순서'] = df['날짜형'].dt.strftime('%Y-%m')
    return df

df_main = format_date(df_main_raw, '수납일')
df_comm = format_date(df_comm_raw, '날짜')

all_dates_df = pd.concat([
    df_main[['월순서', '매출월']] if not df_main.empty and '월순서' in df_main.columns else pd.DataFrame(),
    df_comm[['월순서', '매출월']] if not df_comm.empty and '월순서' in df_comm.columns else pd.DataFrame()
]).drop_duplicates().sort_values('월순서')
CHRONOLOGICAL_MONTHS = all_dates_df['매출월'].dropna().tolist()

# 🔥 Color Map
extended_colors = (px.colors.qualitative.Pastel + px.colors.qualitative.Set3 + px.colors.qualitative.Set2 + px.colors.qualitative.Safe) * 10 
all_nations = sorted(pd.concat([df_main['국적'] if not df_main.empty else pd.Series(), df_comm['국적'] if not df_comm.empty else pd.Series()]).dropna().unique())
NATION_COLOR_MAP = {nation: extended_colors[i] for i, nation in enumerate(all_nations)}
if '중국' in NATION_COLOR_MAP: NATION_COLOR_MAP['중국'] = '#81C784'
if '일본' in NATION_COLOR_MAP: NATION_COLOR_MAP['일본'] = '#64B5F6'
all_regions = sorted(df_main['권역'].dropna().unique()) if not df_main.empty else []
REGION_COLOR_MAP = {region: extended_colors[i] for i, region in enumerate(all_regions)}
all_agents = sorted(df_comm['에이전트'].dropna().unique()) if not df_comm.empty else []
AGENT_COLOR_MAP = {agent: extended_colors[i] for i, agent in enumerate(all_agents)}

st.sidebar.title("🏨 온리프 해외 매출")
menu = st.sidebar.radio("메뉴 이동", ["🌐 온리프 해외매출 전체", "💸 수수료 매출(에이전트별)"])
month_list = sorted(CHRONOLOGICAL_MONTHS, reverse=True)

if not month_list:
    st.error("데이터에서 날짜 정보를 찾을 수 없습니다.")
else:
    # 🎛️ 기간 조회 필터
    sel_month = st.sidebar.selectbox("📅 상세 조회 월 선택", month_list)
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 트렌드 차트 기간 설정")
    default_start = CHRONOLOGICAL_MONTHS[-6] if len(CHRONOLOGICAL_MONTHS) >= 6 else CHRONOLOGICAL_MONTHS[0]
    default_end = CHRONOLOGICAL_MONTHS[-1]
    start_month, end_month = st.sidebar.select_slider("조회할 기간 선택", options=CHRONOLOGICAL_MONTHS, value=(default_start, default_end))
    start_idx, end_idx = CHRONOLOGICAL_MONTHS.index(start_month), CHRONOLOGICAL_MONTHS.index(end_month)
    FILTERED_MONTHS = CHRONOLOGICAL_MONTHS[start_idx : end_idx + 1]

    # ==========================================================
    # --- 메뉴 1: 온리프 해외매출 전체 ---
    # ==========================================================
    if menu == "🌐 온리프 해외매출 전체":
        st.title(f"🌐 {sel_month} 온리프 해외매출 전체")
        view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
        group_col = '국적' if view_mode == "국가별" else '권역'
        current_color_map = NATION_COLOR_MAP if view_mode == "국가별" else REGION_COLOR_MAP

        if '매출월' in df_main.columns:
            m_df = df_main[df_main['매출월'] == sel_month]
            total_rev = m_df['매출액_숫자'].sum()
            curr_comm_df = df_comm[df_comm['매출월'] == sel_month] if not df_comm.empty else pd.DataFrame()
            comm_rev = curr_comm_df['매출액'].sum() if not curr_comm_df.empty else 0
            non_comm_rev = total_rev - comm_rev
            anpa_fee = total_rev * 0.20
            
            # --- 🚀 1. YTD (연누적) 계산 ---
            target_year_prefix = "20" + sel_month[:2] # 예: "2024"
            curr_month_order = all_dates_df[all_dates_df['매출월'] == sel_month]['월순서'].values[0]
            
            # 당해년도 YTD
            ytd_df = df_main[(df_main['월순서'].str.startswith(target_year_prefix)) & (df_main['월순서'] <= curr_month_order)]
            ytd_total = ytd_df['매출액_숫자'].sum()
            
            # 전년도 YTD (성장률 비교용)
            prev_year_prefix = str(int(target_year_prefix) - 1)
            prev_y_month_order = curr_month_order.replace(target_year_prefix, prev_year_prefix)
            pytd_df = df_main[(df_main['월순서'].str.startswith(prev_year_prefix)) & (df_main['월순서'] <= prev_y_month_order)]
            pytd_total = pytd_df['매출액_숫자'].sum()
            ytd_growth = (ytd_total - pytd_total) / pytd_total * 100 if pytd_total > 0 else 0
            # ---------------------------

            idx = month_list.index(sel_month)
            prev_total, growth_rate = 0, 0
            prev_comm_rev, prev_non_comm_rev, prev_anpa_fee = 0, 0, 0
            comm_growth, non_comm_growth, anpa_growth = 0, 0, 0
            
            if idx < len(month_list) - 1:
                prev_month = month_list[idx + 1]
                prev_m_df = df_main[df_main['매출월'] == prev_month]
                prev_total = prev_m_df['매출액_숫자'].sum()
                prev_comm_df = df_comm[df_comm['매출월'] == prev_month] if not df_comm.empty else pd.DataFrame()
                prev_comm_rev = prev_comm_df['매출액'].sum() if not prev_comm_df.empty else 0
                prev_non_comm_rev = prev_total - prev_comm_rev
                prev_anpa_fee = prev_total * 0.20
                if prev_total > 0: growth_rate = (total_rev - prev_total) / prev_total * 100
                if prev_comm_rev > 0: comm_growth = (comm_rev - prev_comm_rev) / prev_comm_rev * 100
                if prev_non_comm_rev > 0: non_comm_growth = (non_comm_rev - prev_non_comm_rev) / prev_non_comm_rev * 100
                if prev_anpa_fee > 0: anpa_growth = (anpa_fee - prev_anpa_fee) / prev_anpa_fee * 100

            # 🔥 UI 카드 레이아웃 (YTD 추가)
            m1, m_ytd, m2, m3, m_space, m4 = st.columns([1, 1.2, 1, 1, 0.2, 1.2])
            with m1:
                st.metric("당월 총 매출액", f"{total_rev:,.0f}원", f"{growth_rate:.1f}%" if prev_total > 0 else None)
            with m_ytd:
                st.metric(f"📅 {target_year_prefix}년 누적(YTD)", f"{ytd_total:,.0f}원", f"{ytd_growth:+.1f}% (YoY)" if pytd_total > 0 else None)
            with m2:
                st.metric("수수료 미지급", f"{non_comm_rev:,.0f}원", f"{non_comm_growth:.1f}%" if prev_non_comm_rev > 0 else None)
            with m3:
                st.metric("수수료 지급", f"{comm_rev:,.0f}원", f"{comm_growth:.1f}%" if prev_comm_rev > 0 else None)
            with m_space:
                st.markdown("<div style='border-left: 2px solid #e0e0e0; height: 80px; margin: auto; width: 2px;'></div>", unsafe_allow_html=True)
            with m4:
                st.metric("💡 앤파 컨설팅(20%)", f"{anpa_fee:,.0f}원", f"{anpa_growth:.1f}%" if prev_anpa_fee > 0 else None)
                
            st.markdown("<br>", unsafe_allow_html=True)
            with st.container():
                st.markdown("### 💡 AI 자동 분석 리포트")
                if prev_total > 0:
                    diff_amt = total_rev - prev_total
                    if growth_rate > 0: st.success(f"📈 **전월 대비 총매출이 성장했습니다!** (+{diff_amt:,.0f}원 / +{growth_rate:.1f}%)")
                    elif growth_rate < 0: st.warning(f"📉 **전월 대비 총매출이 감소했습니다.** ({diff_amt:,.0f}원 / {growth_rate:.1f}%)")
                    if total_rev == df_main.groupby('매출월')['매출액_숫자'].sum().max(): st.info("🏆 **역대 최고 월 매출 기록!**")
                else: st.info("비교 데이터 없음")
            st.divider()

            c1, c2 = st.columns([1, 1.2])
            with c1:
                n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
                n_df = n_df[n_df['매출액_숫자'] > 0]
                pie_total = n_df['매출액_숫자'].sum()
                fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color=group_col, color_discrete_map=current_color_map)
                fig_pie.update_traces(textinfo='percent+label')
                fig_pie.update_layout(annotations=[dict(text=f"총 매출액<br><b>{pie_total:,.0f}원</b>", x=0.5, y=0.5, font_size=13, showarrow=False)])
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with c2:
                st.subheader(f"📑 {view_mode} 상세 실적")
                def format_diff_func(row):
                    c, p, d = row['당월매출'], row['전월매출'], row['증감액']
                    if p == 0 and c > 0: return f"+{int(d):,} (순증가)"
                    if d == 0: return "-"
                    rate = (d / p) * 100
                    return f"{'+' if d > 0 else ''}{int(d):,} ({'🔺 ' if d > 0 else '🔻 '}{abs(rate):.1f}%)"

                curr_group = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '당월매출'})
                if idx < len(month_list) - 1:
                    prev_group = df_main[df_main['매출월'] == month_list[idx+1]].groupby(group_col)['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '전월매출'})
                    table_df = pd.merge(curr_group, prev_group, on=group_col, how='outer').fillna(0)
                else:
                    table_df = curr_group.copy(); table_df['전월매출'] = 0

                table_df['증감액'] = table_df['당월매출'] - table_df['전월매출']
                table_df = table_df.sort_values('당월매출', ascending=False)
                total_row = pd.DataFrame([{group_col: '[ 총 합계 ]', '당월매출': table_df['당월매출'].sum(), '전월매출': table_df['전월매출'].sum(), '증감액': table_df['증감액'].sum()}])
                table_df = pd.concat([table_df, total_row], ignore_index=True)
                table_df[f'{sel_month}'] = table_df['당월매출'].apply(lambda x: f"{int(x):,}")
                if idx < len(month_list) - 1:
                    table_df[f'{month_list[idx+1]}(전월)'] = table_df['전월매출'].apply(lambda x: f"{int(x):,}")
                    table_df['전월대비'] = table_df.apply(format_diff_func, axis=1)
                    display_cols = [group_col, f'{month_list[idx+1]}(전월)', f'{sel_month}', '전월대비']
                else:
                    display_cols = [group_col, f'{sel_month}']
                st.dataframe(table_df[display_cols], use_container_width=True, hide_index=True)

            st.divider()
            st.subheader(f"📈 전체 월별 성장 추이 ({view_mode} 기준)")
            filtered_main = df_main[df_main['매출월'].isin(FILTERED_MONTHS)]
            trend_df = filtered_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            fig = go.Figure()
            for item in trend_df[group_col].unique():
                d = trend_df[trend_df[group_col] == item]
                fig.add_trace(go.Bar(x=d['매출월'], y=d['매출액_숫자'], name=item, text=item, textposition='auto', marker_color=current_color_map.get(item, '#cccccc')))
            tot_series = filtered_main.groupby('매출월')['매출액_숫자'].sum().reindex(FILTERED_MONTHS).fillna(0)
            fig.add_trace(go.Scatter(x=tot_series.index, y=tot_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}백" for v in tot_series.values], textposition="top center"))
            t_vals, t_txts = get_dynamic_ticks(tot_series.max())
            fig.update_layout(barmode='stack', hovermode="x unified", xaxis={'categoryorder': 'array', 'categoryarray': FILTERED_MONTHS}, yaxis=dict(tickmode='array', tickvals=t_vals, ticktext=t_txts), bargap=0.45)
            st.plotly_chart(fig, use_container_width=True)

    # ==========================================================
    # --- 메뉴 2: 수수료 매출 (에이전트별) ---
    # ==========================================================
    else:
        agent_options = ["전체"] + sorted(df_comm['에이전트'].dropna().unique().tolist())
        sel_agent = st.sidebar.selectbox("🧑‍💼 에이전트 상세 필터", agent_options)
        page_df = df_comm.copy() if sel_agent == "전체" else df_comm[df_comm['에이전트'] == sel_agent].copy()
        g_col = '에이전트' if sel_agent == "전체" else '국적'
        st.title(f"💸 {sel_month} {'수수료 매출 전체 분석' if sel_agent == '전체' else f'[{sel_agent}] 상세 분석'}")
        
        if not page_df.empty:
            curr_comm = page_df[page_df['매출월'] == sel_month]
            total_comm_rev = curr_comm['매출액'].sum()
            c_paid_comm = curr_comm['지급수수료'].sum()
            c_net_rev = curr_comm['실매출액'].sum()
            
            idx = month_list.index(sel_month)
            p_comm_total, p_paid_comm, p_net_rev = 0, 0, 0
            c_growth, paid_growth, net_growth = 0, 0, 0
            if idx < len(month_list) - 1:
                p_df = page_df[page_df['매출월'] == month_list[idx+1]]
                p_comm_total, p_paid_comm, p_net_rev = p_df['매출액'].sum(), p_df['지급수수료'].sum(), p_df['실매출액'].sum()
                if p_comm_total > 0: c_growth = (total_comm_rev - p_comm_total) / p_comm_total * 100
                if p_paid_comm > 0: paid_growth = (c_paid_comm - p_paid_comm) / p_paid_comm * 100
                if p_net_rev > 0: net_growth = (c_net_rev - p_net_rev) / p_net_rev * 100

            m1, m2, m3 = st.columns(3)
            with m1: st.metric("총 수납액", f"{total_comm_rev:,.0f}원", f"{c_growth:.1f}%" if p_comm_total > 0 else None)
            with m2: st.metric("지급수수료", f"{c_paid_comm:,.0f}원", f"{paid_growth:.1f}%" if p_paid_comm > 0 else None)
            with m3: st.metric("실매출액", f"{c_net_rev:,.0f}원", f"{net_growth:.1f}%" if p_net_rev > 0 else None)

            st.divider()
            filtered_page = page_df[page_df['매출월'].isin(FILTERED_MONTHS)]
            trend_data = filtered_page.groupby(['월순서', '매출월', g_col])['매출액'].sum().reset_index().sort_values('월순서')
            fig_ctrend = go.Figure()
            for g_item in trend_data[g_col].unique():
                a_data = trend_data[trend_data[g_col] == g_item]
                fig_ctrend.add_trace(go.Bar(x=a_data['매출월'], y=a_data['매출액'], name=g_item, text=g_item, textposition='auto', marker_color=AGENT_COLOR_MAP.get(g_item, '#ccc') if sel_agent == "전체" else NATION_COLOR_MAP.get(g_item, '#ccc')))
            total_cline = filtered_page.groupby('매출월')['매출액'].sum().reindex(FILTERED_MONTHS).fillna(0)
            fig_ctrend.add_trace(go.Scatter(x=total_cline.index, y=total_cline.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}백" for v in total_cline.values], textposition="top center"))
            c_vals, c_txts = get_dynamic_ticks(total_cline.max())
            fig_ctrend.update_layout(barmode='stack', hovermode="x unified", xaxis={'categoryorder': 'array', 'categoryarray': FILTERED_MONTHS}, yaxis=dict(tickmode='array', tickvals=c_vals, ticktext=c_txts), bargap=0.45)
            st.plotly_chart(fig_ctrend, use_container_width=True)
