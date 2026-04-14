import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 데이터 주소
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = {
    "레이블": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "The SC": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "천수현 대표": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "앤티스": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv"
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
            comm_list.append(df_c)
        except: continue
    df_comm_total = pd.concat(comm_list, ignore_index=True) if comm_list else pd.DataFrame()
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

st.sidebar.title("🏨 온리프 관리 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🌐 온리프 해외매출 전체", "💸 수수료 매출(에이전트별)"])
month_list = sorted(CHRONOLOGICAL_MONTHS, reverse=True)

if not month_list:
    st.error("데이터에서 날짜 정보를 찾을 수 없습니다.")
else:
    sel_month = st.sidebar.selectbox("📅 조회 월 선택", month_list)

    # ==========================================================
    # --- 메뉴 1: 온리프 해외매출 전체 ---
    # ==========================================================
    if menu == "🌐 온리프 해외매출 전체":
        st.title(f"🌐 {sel_month} 온리프 해외매출 전체")
        view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
        group_col = '국적' if view_mode == "국가별" else '권역'

        if '매출월' in df_main.columns:
            m_df = df_main[df_main['매출월'] == sel_month]
            total_rev = m_df['매출액_숫자'].sum()
            idx = month_list.index(sel_month)
            prev_total, prev_month, growth_rate = 0, "", 0
            
            if idx < len(month_list) - 1:
                prev_month = month_list[idx + 1]
                prev_m_df = df_main[df_main['매출월'] == prev_month]
                prev_total = prev_m_df['매출액_숫자'].sum()
                if prev_total > 0: growth_rate = (total_rev - prev_total) / prev_total * 100

            if prev_total > 0: st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원", f"{growth_rate:.1f}%")
            else: st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원")

            with st.container():
                st.markdown("### 💡 AI 자동 분석 리포트")
                if prev_total > 0:
                    diff_amt = total_rev - prev_total
                    if growth_rate > 0: st.success(f"📈 **전월 대비 총매출이 성장했습니다!** (+{diff_amt:,.0f}원 / +{growth_rate:.1f}%)")
                    elif growth_rate < 0: st.warning(f"📉 **전월 대비 총매출이 감소했습니다.** ({diff_amt:,.0f}원 / {growth_rate:.1f}%)")
                    if total_rev == df_main.groupby('매출월')['매출액_숫자'].sum().max(): st.info("🏆 **역대 최고 월 매출 기록!**")
                        
                    curr_nations = m_df.groupby('국적')['매출액_숫자'].sum()
                    prev_nations = prev_m_df.groupby('국적')['매출액_숫자'].sum()
                    growth_nations = curr_nations.subtract(prev_nations, fill_value=0)
                    
                    if not growth_nations.empty and growth_nations.max() > 0:
                        top_nation = growth_nations.idxmax()
                        top_growth_amt = growth_nations.max()
                        prev_amt = prev_nations.get(top_nation, 0)
                        rate_str = f" / +{(top_growth_amt / prev_amt * 100):.1f}%" if prev_amt > 0 else " / 순증가(신규)"
                        st.info(f"🔥 **가장 눈에 띄는 성장 국가:** **{top_nation}** (전월 대비 +{top_growth_amt:,.0f}원{rate_str})")
                else: st.info("비교 데이터 없음")
            st.divider()

            # ==========================================
            # 🌊 전월 대비 워터폴 차트 추가
            # ==========================================
            if prev_total > 0:
                st.subheader(f"🌊 전월 대비 {view_mode} 매출 증감 워터폴")
                
                curr_series = m_df.groupby(group_col)['매출액_숫자'].sum()
                prev_series = prev_m_df.groupby(group_col)['매출액_숫자'].sum()
                
                diff_series = curr_series.subtract(prev_series, fill_value=0).sort_values(ascending=False)
                
                wf_x = [f"{prev_month}<br>(전월)"]
                wf_y = [prev_total]
                wf_measure = ["absolute"]
                
                for item, diff in diff_series.items():
                    if diff != 0:
                        wf_x.append(str(item))
                        wf_y.append(diff)
                        wf_measure.append("relative")
                        
                wf_x.append(f"{sel_month}<br>(당월)")
                wf_y.append(total_rev)
                wf_measure.append("total")
                
                fig_wf = go.Figure(go.Waterfall(
                    name="MoM 증감",
                    orientation="v",
                    measure=wf_measure,
                    x=wf_x,
                    y=wf_y,
                    textposition="outside",
                    text=[f"{v:,.0f}" if v != 0 else "" for v in wf_y],
                    decreasing={"marker": {"color": "#FF6B6B"}},
                    increasing={"marker": {"color": "#4ECDC4"}},
                    totals={"marker": {"color": "#45B7D1"}}
                ))
                
                fig_wf.update_layout(
                    waterfallgap=0.3,
                    showlegend=False,
                    height=450,
                    margin=dict(t=30, b=30)
                )
                
                st.plotly_chart(fig_wf, use_container_width=True)
                st.divider()
            # ==========================================

            c1, c2 = st.columns([1, 1.2])
            with c1:
                n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
                n_df = n_df[n_df['매출액_숫자'] > 0]
                st.plotly_chart(px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel).update_traces(textinfo='percent+label'), use_container_width=True)
            with c2:
                st.subheader(f"📑 {view_mode} 상세 실적")
                st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                
                table_df = n_df.sort_values('매출액_숫자', ascending=False)
                total_sum = table_df['매출액_숫자'].sum()
                total_row = pd.DataFrame([{group_col: '[ 총 합계 ]', '매출액_숫자': total_sum}])
                table_df = pd.concat([table_df, total_row], ignore_index=True)
                
                table_df['매출액(원)'] = table_df['매출액_숫자'].apply(lambda x: f"{int(x):,}")
                st.dataframe(table_df[[group_col, '매출액(원)']], use_container_width=True, hide_index=True, column_config={"매출액(원)": st.column_config.TextColumn(alignment="right")})
            
            if view_mode == "권역별":
                etc = m_df[m_df['권역'] == '기타']['국적'].dropna().unique()
                if len(etc) > 0:
                    with st.expander("ℹ️ '기타' 권역 구성 국가 확인"): st.write(", ".join(etc))

            st.divider()
            st.subheader(f"📈 전체 월별 성장 추이 ({view_mode} 기준)")
            trend_df = df_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            fig = go.Figure()
            for item in trend_df[group_col].unique():
                d = trend_df[trend_df[group_col] == item]
                fig.add_trace(go.Bar(x=d['매출월'], y=d['매출액_숫자'], name=item, text=item, textposition='auto'))
            
            tot_series = df_main.groupby('매출월')['매출액_숫자'].sum().reindex(CHRONOLOGICAL_MONTHS).fillna(0)
            fig.add_trace(go.Scatter(x=tot_series.index, y=tot_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}M" for v in tot_series.values], textposition="top center"))
            
            st.plotly_chart(fig.update_layout(barmode='stack', hovermode="x unified", xaxis={'categoryorder': 'array', 'categoryarray': CHRONOLOGICAL_MONTHS}, bargap=0.45), use_container_width=True)

    # ==========================================================
    # --- 메뉴 2: 수수료 매출 (에이전트별) ---
    # ==========================================================
    else:
        agent_options = ["전체"] + sorted(df_comm['에이전트'].dropna().unique().tolist())
        sel_agent = st.sidebar.selectbox("🧑‍💼 에이전트 상세 필터", agent_options)

        if sel_agent == "전체":
            page_df = df_comm.copy()
            g_col = '에이전트'
            page_title = "수수료 매출 전체 분석"
        else:
            page_df = df_comm[df_comm['에이전트'] == sel_agent].copy()
            g_col = '국적'
            page_title = f"[{sel_agent}] 에이전트 상세 분석"

        st.title(f"💸 {sel_month} {page_title}")
        
        if not page_df.empty:
            curr_comm = page_df[page_df['매출월'] == sel_month]
            total_comm_rev = curr_comm['매출액'].sum()
            
            idx = month_list.index(sel_month)
            p_comm_total, p_month, c_growth_rate = 0, "", 0
            if idx < len(month_list) - 1:
                p_month = month_list[idx + 1]
                p_comm_df = page_df[page_df['매출월'] == p_month]
                p_comm_total = p_comm_df['매출액'].sum()
                if p_comm_total > 0: c_growth_rate = (total_comm_rev - p_comm_total) / p_comm_total * 100

            metric_title = "총 수납액 합계" if sel_agent == "전체" else f"[{sel_agent}] 총 수납액"
            if p_comm_total > 0: st.metric(metric_title, f"{total_comm_rev:,.0f}원", f"{c_growth_rate:.1f}%")
            else: st.metric(metric_title, f"{total_comm_rev:,.0f}원")

            with st.container():
                st.markdown(f"### 💡 AI 실적 분석 리포트")
                if p_comm_total > 0:
                    c_diff_amt = total_comm_rev - p_comm_total
                    if c_growth_rate > 0: st.success(f"📈 **전월 대비 수납액이 증가했습니다!** (+{c_diff_amt:,.0f}원 / +{c_growth_rate:.1f}%)")
                    elif c_growth_rate < 0: st.warning(f"📉 **전월 대비 수납액이 감소했습니다.** ({c_diff_amt:,.0f}원 / {c_growth_rate:.1f}%)")
                    
                    if total_comm_rev == page_df.groupby('매출월')['매출액'].sum().max() and total_comm_rev > 0: 
                        st.info(f"🏆 **역대 최고치 경신!**")
                    
                    c_groups = curr_comm.groupby(g_col)['매출액'].sum()
                    p_groups = p_comm_df.groupby(g_col)['매출액'].sum()
                    group_diff = c_groups.subtract(p_groups, fill_value=0)
                    
                    label_name = "에이전트" if sel_agent == "전체" else "국가"
                    
                    if not group_diff.empty:
                        top_g = group_diff.idxmax()
                        top_diff_amt = group_diff.max()
                        bottom_g = group_diff.idxmin()
                        bottom_diff_amt = group_diff.min()

                        if top_diff_amt > 0:
                            p_g_amt = p_groups.get(top_g, 0)
                            a_rate_str = f" / +{(top_diff_amt / p_g_amt * 100):.1f}%" if p_g_amt > 0 else " / 순증가(신규)"
                            st.info(f"🚀 **최대 성장 {label_name}:** **{top_g}** (전월 대비 +{top_diff_amt:,.0f}원{a_rate_str})")
                            
                        if bottom_diff_amt < 0:
                            p_g_amt_bottom = p_groups.get(bottom_g, 0)
                            b_rate_str = f" / {(bottom_diff_amt / p_g_amt_bottom * 100):.1f}%" if p_g_amt_bottom > 0 else ""
                            st.error(f"🔻 **최대 감소 {label_name}:** **{bottom_g}** (전월 대비 {bottom_diff_amt:,.0f}원{b_rate_str})")
                else: st.info("비교 데이터가 부족하여 분석을 생략합니다.")
            st.divider()

            chart_subtitle = "에이전트별 누적" if sel_agent == "전체" else "국가(국적)별 누적"
            st.subheader(f"📈 월별 수수료 매출 추이 ({chart_subtitle})")
            trend_data = page_df.groupby(['월순서', '매출월', g_col])['매출액'].sum().reset_index().sort_values('월순서')
            fig_ctrend = go.Figure()
            for g_item in trend_data[g_col].unique():
                a_data = trend_data[trend_data[g_col] == g_item]
                fig_ctrend.add_trace(go.Bar(x=a_data['매출월'], y=a_data['매출액'], name=g_item, text=g_item, textposition='auto'))
            
            total_cline_series = page_df.groupby('매출월')['매출액'].sum().reindex(CHRONOLOGICAL_MONTHS).fillna(0)
            fig_ctrend.add_trace(go.Scatter(x=total_cline_series.index, y=total_cline_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}M" for v in total_cline_series.values], textposition="top center"))
            
            st.plotly_chart(fig_ctrend.update_layout(barmode='stack', hovermode="x unified", height=500, xaxis={'categoryorder': 'array', 'categoryarray': CHRONOLOGICAL_MONTHS}, bargap=0.45), use_container_width=True)

            st.divider()
            
            if sel_agent == "전체":
                st.subheader(f"🗺️ {sel_month} 에이전트별 국가 구성비")
                if not curr_comm.empty:
                    comp = curr_comm.groupby(['에이전트', '국적'])['매출액'].sum().reset_index()
                    comp = comp[comp['매출액'] > 0]
                    st.plotly_chart(px.bar(comp, x='매출액', y='에이전트', color='국적', orientation='h', text='국적', color_discrete_sequence=px.colors.qualitative.Pastel).update_traces(textposition='inside').update_layout(barmode='stack', height=400), use_container_width=True)
                    
                    st.subheader("📑 상세 정산 내역")
                    st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                    table_comm = curr_comm.groupby(['에이전트', '국적'])['매출액'].sum().reset_index()
                    table_comm = table_comm[table_comm['매출액'] > 0].sort_values(['에이전트', '매출액'], ascending=[True, False])
                    total_comm_sum = table_comm['매출액'].sum()
                    total_row_comm = pd.DataFrame([{'에이전트': '[ 총 합계 ]', '국적': '-', '매출액': total_comm_sum}])
                    table_comm = pd.concat([table_comm, total_row_comm], ignore_index=True)
                    table_comm['매출액(원)'] = table_comm['매출액'].apply(lambda x: f"{int(x):,}")
                    st.dataframe(table_comm[['에이전트', '국적', '매출액(원)']], use_container_width=True, hide_index=True, column_config={"매출액(원)": st.column_config.TextColumn(alignment="right")})
            else:
                st.subheader(f"🗺️ {sel_month} [{sel_agent}] 소속 국가 구성비")
                if not curr_comm.empty:
                    col1, col2 = st.columns([1, 1.2])
                    
                    with col1:
                        comp = curr_comm.groupby(['국적'])['매출액'].sum().reset_index()
                        comp = comp[comp['매출액'] > 0]
                        fig_comp = px.pie(comp, values='매출액', names='국적', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig_comp.update_traces(textinfo='percent+label')
                        st.plotly_chart(fig_comp, use_container_width=True)
                        
                    with col2:
                        st.subheader("📑 상세 정산 내역")
                        st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
                        table_comm = curr_comm.groupby(['국적'])['매출액'].sum().reset_index()
                        table_comm = table_comm[table_comm['매출액'] > 0].sort_values(['매출액'], ascending=False)
                        total_comm_sum = table_comm['매출액'].sum()
                        total_row_comm = pd.DataFrame([{'국적': '[ 총 합계 ]', '매출액': total_comm_sum}])
                        table_comm = pd.concat([table_comm, total_row_comm], ignore_index=True)
                        table_comm['매출액(원)'] = table_comm['매출액'].apply(lambda x: f"{int(x):,}")
                        st.dataframe(table_comm[['국적', '매출액(원)']], use_container_width=True, hide_index=True, column_config={"매출액(원)": st.column_config.TextColumn(alignment="right")})
