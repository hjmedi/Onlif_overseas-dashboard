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
COMMISSION_URLS = [
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=344598450&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv"
]

# 🌍 권역 매핑 함수 (복구)
def get_region(nation):
    nation = str(nation).strip()
    if nation in ['중국', '대만', '홍콩', '마카오', 'China', 'Taiwan', 'Hong Kong']: return '중화권'
    elif nation in ['일본', 'Japan']: return '일본'
    elif nation in ['태국', '베트남', '싱가포르', '필리핀', '말레이시아', '인도네시아', '미얀마', '캄보디아', '라오스', 'Singapore', 'Thailand', 'Vietnam']: return '동남아'
    elif nation in ['미국', '캐나다', 'USA', 'Canada', 'United States']: return '북미'
    elif nation in ['영국', '프랑스', '독일', '이탈리아', '스페인', '러시아', '네덜란드', 'UK', 'France', 'Germany']: return '유럽'
    else: return '기타'

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30)
def load_data():
    # 1. 메인 데이터 로드
    res_main = requests.get(URL_MAIN)
    raw_main = pd.read_csv(StringIO(res_main.content.decode('utf-8-sig')), header=None)
    
    h_idx = 0
    for i in range(len(raw_main)):
        row_str = "".join(raw_main.iloc[i].fillna('').astype(str))
        if '이름' in row_str and '국적' in row_str:
            h_idx = i
            break
    
    df_m = raw_main.copy()
    df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna('미지정')]
    df_m = df_m.drop(range(h_idx + 1)).reset_index(drop=True)
    
    div_col = [c for c in df_m.columns if '구분' in c]
    if div_col:
        df_m = df_m[df_m[div_col[0]].astype(str).str.contains('해외', na=False)]
    
    # 2. 수수료 데이터 로드
    all_comm = []
    for url in COMMISSION_URLS:
        try:
            r = requests.get(url)
            all_comm.append(pd.read_csv(StringIO(r.content.decode('utf-8-sig'))))
        except: continue
    df_c = pd.concat(all_comm, ignore_index=True) if all_comm else pd.DataFrame()
    
    return df_m, df_c

df_main, df_comm = load_data()

# --- 공통 전처리 ---
def process_df(df, is_main=True):
    date_col = [c for c in df.columns if '수납일' in c]
    if date_col:
        df['날짜형식'] = pd.to_datetime(df[date_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형식'])
        df['매출월'] = df['날짜형식'].dt.strftime('%y년 %m월')
        df['월순서'] = df['날짜형식'].dt.to_period('M')
    
    if is_main:
        amt_col = [c for c in df.columns if '수납액' in c and 'CRM' in c]
        df['매출액_숫자'] = df[amt_col[0]].apply(to_numeric) / 1.1 if amt_col else 0
        df['권역'] = df['국적'].apply(get_region)
    else:
        rev_col = [c for c in df.columns if '수납액' in c]
        fee_col = [c for c in df.columns if '수수료' in c or '정산금' in c]
        if rev_col: df['r_num'] = df[rev_col[0]].apply(to_numeric)
        if fee_col: df['f_num'] = df[fee_col[0]].apply(to_numeric)
    return df

df_main = process_df(df_main, is_main=True)
if not df_comm.empty:
    df_comm = process_df(df_comm, is_main=False)

# --- 사이드바 ---
st.sidebar.title("🏨 온리프 관리 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🌐 전체 매출 요약", "💸 수수료 매출 분석"])
sel_month = st.sidebar.selectbox("📅 조회 월 선택", sorted(df_main['매출월'].unique(), reverse=True))

# --- 메뉴 1: 전체 매출 요약 ---
if menu == "🌐 전체 매출 요약":
    st.title(f"🌐 {sel_month} 국적 및 권역별 매출 요약")
    view_mode = st.sidebar.radio("🔎 분석 기준", ["국가별", "권역별"])
    group_col = '국적' if view_mode == "국가별" else '권역'
    
    m_df = df_main[df_main['매출월'] == sel_month]
    total_rev = m_df['매출액_숫자'].sum()
    st.metric("총 매출액 (VAT 제외)", f"{total_rev:,.0f}원")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        n_df = m_df.groupby(group_col)['매출액_숫자'].sum().reset_index()
        fig_pie = px.pie(n_df, values='매출액_숫자', names=group_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
    with c2:
        st.subheader(f"📑 {view_mode} 상세 실적")
        st.markdown("<p style='text-align: right; color: gray; font-size: 0.8rem;'>(단위: 원)</p>", unsafe_allow_html=True)
        table_df = n_df.sort_values('매출액_숫자', ascending=False)
        table_df['매출액'] = table_df['매출액_숫자'].apply(lambda x: f"{int(x):,}")
        st.dataframe(table_df[[group_col, '매출액']], use_container_width=True, hide_index=True,
                     column_config={"매출액": st.column_config.TextColumn(alignment="right")})

    # 📈 월별 성장 추이 (복구)
    st.divider()
    st.subheader(f"📈 월별 성장 추이 ({view_mode} 기준)")
    trend_df = df_main.groupby(['월순서', '매출월', group_col])['매출액_숫자'].sum().reset_index().sort_values('월순서')
    fig_trend = px.bar(trend_df, x='매출월', y='매출액_숫자', color=group_col, text_auto='.2s')
    fig_trend.update_layout(barmode='stack')
    st.plotly_chart(fig_trend, use_container_width=True)

# --- 메뉴 2: 수수료 분석 ---
else:
    st.title(f"💸 {sel_month} 수수료 및 유입 경로 분석")
    if not df_comm.empty:
        c_df = df_comm[df_comm['매출월'] == sel_month]
        t_rev = c_df['r_num'].sum()
        t_fee = c_df['f_num'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("총 수납액", f"{t_rev:,.0f}원")
        m2.metric("총 수수료", f"{t_fee:,.0f}원")
        m3.metric("수수료 비중", f"{(t_fee/t_rev*100):.1f}%" if t_rev>0 else "0%")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            path_col = [c for c in c_df.columns if '유입경로' in c][0]
            p_df = c_df.groupby(path_col)['f_num'].sum().reset_index()
            st.plotly_chart(px.pie(p_df, values='f_num', names=path_col, hole=0.4, title="경로별 수수료 비중"), use_container_width=True)
        with col2:
            # 월별 수수료 추이
            c_trend = df_comm.groupby(['월순서', '매출월']).agg({'r_num':'sum', 'f_num':'sum'}).reset_index().sort_values('월순서')
            fig_c_trend = go.Figure()
            fig_c_trend.add_trace(go.Bar(x=c_trend['매출월'], y=c_trend['r_num'], name='총 수납액'))
            fig_c_trend.add_trace(go.Bar(x=c_trend['매출월'], y=c_trend['f_num'], name='수수료'))
            st.plotly_chart(fig_c_trend, use_container_width=True)

        st.subheader("📋 수수료 상세 리스트")
        c_df['수납액'] = c_df['r_num'].apply(lambda x: f"{int(x):,}")
        c_df['수수료'] = c_df['f_num'].apply(lambda x: f"{int(x):,}")
        st.dataframe(c_df[['수납일', '이름', path_col, '수납액', '수수료']], use_container_width=True, hide_index=True,
                     column_config={"수납액": st.column_config.TextColumn(alignment="right"), "수수료": st.column_config.TextColumn(alignment="right")})
