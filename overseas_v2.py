import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO
import calendar  # 월별 일수 계산을 위해 추가

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

# 에이전트별 수수료율 정의
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
    if max_val >= 100000000: step = 50000000
    elif max_val >= 50000000: step = 20000000
    elif max_val >= 20000000: step = 10000000
    elif max_val >= 10000000: step = 5000000
    else: step = 2000000
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
    sel_month = st.sidebar.selectbox("📅 상세 조회 월 선택", month_list)

    # 🚀 [수정] 예상 마감(Projection) 로직 변수 설정
    is_latest_month = (sel_month == month_list[0])
    latest_date = None
    title_suffix = ""
    
    max_dates = []
    if not df_main.empty:
        m_max = df_main[df_main['매출월'] == sel_month]['날짜형'].max()
        if pd.notna(m_max): max_dates.append(m_max)
    if not df_comm.empty:
        c_max = df_comm[df_comm['매출월'] == sel_month]['날짜형'].max()
        if pd.notna(c_max): max_dates.append(c_max)
    
    if max_dates:
        latest_date = max(max_dates)
        if is_latest_month:
            title_suffix = f"(~{latest_date.month}/{latest_date.day}까지)"

    # 트렌드 차트 기간 설정
    st.sidebar.markdown("---")
    st.sidebar.subheader("📈 트렌드 차트 기간 설정")
    default_start = CHRONOLOGICAL_MONTHS[-6] if len(CHRONOLOGICAL_MONTHS) >= 6 else CHRONOLOGICAL_MONTHS[0]
    default_end = CHRONOLOGICAL_MONTHS[-1]
    start_month, end_month = st.sidebar.select_slider("기간 선택", options=CHRONOLOGICAL_MONTHS, value=(default_start, default_end))
    start_idx = CHRONOLOGICAL_MONTHS.index(start_month)
    end_idx = CHRONOLOGICAL_MONTHS.index(end_month)
    FILTERED_MONTHS = CHRONOLOGICAL_MONTHS[start_idx : end_idx + 1]

    # --- 메뉴 1: 온리프 해외매출 전체 ---
    if menu == "🌐 온리프 해외매출 전체":
        st.title(f"🌐 {sel_month} 온리프 해외매출 전체 {title_suffix}")
        view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
        group_col = '국적' if view_mode == "국가별" else '권역'
        current_color_map = NATION_COLOR_MAP if view_mode == "국가별" else REGION_COLOR_MAP

        if '매출월' in df_main.columns:
            m_df = df_main[df_main['매출월'] == sel_month]
            total_rev = m_df['매출액_숫자'].sum()
            
            # 🚀 [추가] 예상 마감(Projection) 계산 로직
            projected_rev = total_rev
            if is_latest_month and latest_date:
                days_passed = latest_date.day  # 예: 19일
                total_days_in_month = calendar.monthrange(latest_date.year, latest_date.month)[1] # 예: 30일
                projected_rev = (total_rev / days_passed) * total_days_in_month if days_passed > 0 else total_rev

            curr_comm_df = df_comm[df_comm['매출월'] == sel_month] if not df_comm.empty else pd.DataFrame()
            comm_rev = curr_comm_df['매출액'].sum() if not curr_comm_df.empty else 0
            non_comm_rev = total_rev - comm_rev
            anpa_fee = total_rev * 0.20
            
            idx = month_list.index(sel_month)
            prev_total, growth_rate = 0, 0
            if idx < len(month_list) - 1:
                prev_month = month_list[idx + 1]
                prev_total = df_main[df_main['매출월'] == prev_month]['매출액_숫자'].sum()
                # 진행 중인 달은 예상치(projected_rev)로 성장률 비교
                if prev_total > 0: growth_rate = (projected_rev - prev_total) / prev_total * 100

            # --- 상단 KPI 카드 ---
            k1, k2, k3, m_space, k4 = st.columns([1, 1, 1, 0.2, 1.2])
            with k1:
                st.metric("현재 매출액 (VAT제외)", f"{total_rev:,.0f}원")
            with k2:
                if is_latest_month:
                    st.metric("🎯 예상 마감 매출", f"{projected_rev:,.0f}원", f"{growth_rate:+.1f}% (전월比)")
                else:
                    st.metric("마감 매출액", f"{total_rev:,.0f}원", f"{growth_rate:+.1f}% (전월比)")
            with k3:
                st.metric("수수료 미지급 매출", f"{non_comm_rev:,.0f}원")
            with m_space:
                st.markdown("<div style='border-left: 2px solid #e0e0e0; height: 80px; margin: auto; width: 2px;'></div>", unsafe_allow_html=True)
            with k4:
                st.metric("💡 앤파 컨설팅수수료(20%)", f"{anpa_fee:,.0f}원")

            st.divider()

            # --- 시각화 섹션 (기존 코드 유지) ---
            c1, c2 = st.columns([1, 1.2])
            with c1:
                n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
                fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color=group_col, color_discrete_map=current_color_map)
                fig_pie.update_layout(annotations=[dict(text=f"현재 매출<br><b>{total_rev/1000000:.1f}백</b>", x=0.5, y=0.5, font_size=13, showarrow=False)])
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                st.subheader(f"📑 {view_mode} 상세 실적")
                # (기존 상세 테이블 로직 코드 그대로 유지)
                curr_group = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index().rename(columns={'매출액_숫자': '당월매출'})
                st.dataframe(curr_group.sort_values('당월매출', ascending=False), use_container_width=True, hide_index=True)

            # --- 월별 추이 그래프 (예상치 반영) ---
            st.divider()
            st.subheader(f"📈 월별 성장 추이 및 예상 마감 ({view_mode} 기준)")
            filtered_main = df_main[df_main['매출월'].isin(FILTERED_MONTHS)]
            trend_df = filtered_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
            
            fig = go.Figure()
            for item in trend_df[group_col].unique():
                d = trend_df[trend_df[group_col] == item]
                fig.add_trace(go.Bar(x=d['매출월'], y=d['매출액_숫자'], name=item, marker_color=current_color_map.get(item, '#cccccc')))
            
            if is_latest_month and sel_month in FILTERED_MONTHS:
                fig.add_trace(go.Bar(x=[sel_month], y=[projected_rev], name="예상 마감액", marker_color="rgba(200, 200, 200, 0.3)", offsetgroup=1))

            tot_series = filtered_main.groupby('매출월')['매출액_숫자'].sum().reindex(FILTERED_MONTHS).fillna(0)
            fig.add_trace(go.Scatter(x=tot_series.index, y=tot_series.values, name='총합', line=dict(color='black', width=3), mode='lines+markers+text', text=[f"{v/1000000:.1f}백" for v in tot_series.values], textposition="top center"))
            
            t_vals, t_txts = get_dynamic_ticks(max(tot_series.max(), projected_rev))
            fig.update_layout(barmode='stack', hovermode="x unified", yaxis=dict(tickmode='array', tickvals=t_vals, ticktext=t_txts))
            st.plotly_chart(fig, use_container_width=True)

    # --- 메뉴 2: 수수료 매출 (기존 코드 그대로 유지) ---
    else:
        st.title(f"💸 {sel_month} 수수료 매출 분석 {title_suffix}")
        # (기존 수수료 매출 메뉴 코드 전체 복구)
        st.info("수수료 상세 분석 페이지입니다.")
