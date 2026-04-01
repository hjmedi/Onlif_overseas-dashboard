import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# 1. 페이지 설정
st.set_page_config(page_title="온리프 해외 매출 통합 관리", layout="wide")

# ✅ 데이터 주소 (그대로 유지)
URL_MAIN = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"
COMMISSION_URLS = [
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1298456060&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3/pub?gid=344598450&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=1973655230&single=true&output=csv",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=2053307016&single=true&output=csv"
]

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=30)
def load_data():
    # 1. 메인 데이터 로드 및 전처리
    res_main = requests.get(URL_MAIN)
    raw_main = pd.read_csv(StringIO(res_main.content.decode('utf-8-sig')), header=None)
    
    # 제목줄 찾기
    h_idx = 0
    for i in range(len(raw_main)):
        row_str = "".join(raw_main.iloc[i].fillna('').astype(str))
        if '이름' in row_str and '국적' in row_str:
            h_idx = i
            break
    
    df_m = raw_main.copy()
    df_m.columns = [str(c).strip() for c in df_m.iloc[h_idx].fillna('미지정')]
    df_m = df_m.drop(range(h_idx + 1)).reset_index(drop=True)
    
    # '구분' 또는 '해외' 관련 컬럼 자동 탐색 (에러 방지 핵심)
    div_col = [c for c in df_m.columns if '구분' in c or '해외' in c]
    if div_col:
        df_m = df_m[df_m[div_col[0]].astype(str).str.contains('해외', na=False)]
    
    # 2. 수수료 데이터 통합 로드
    all_comm = []
    for url in COMMISSION_URLS:
        try:
            r = requests.get(url)
            t_df = pd.read_csv(StringIO(r.content.decode('utf-8-sig')))
            all_comm.append(t_df)
        except: continue
    df_c = pd.concat(all_comm, ignore_index=True) if all_comm else pd.DataFrame()
    
    return df_m, df_c

# 데이터 로드
df_main, df_comm = load_data()

# --- 공통 날짜 처리 ---
def process_date(df, col_name):
    target_col = [c for c in df.columns if col_name in c]
    if target_col:
        df['날짜형식'] = pd.to_datetime(df[target_col[0]], errors='coerce')
        df = df.dropna(subset=['날짜형식'])
        df['매출월'] = df['날짜형식'].dt.strftime('%y년 %m월')
        df['정렬키'] = df['날짜형식'].dt.to_period('M')
    return df

df_main = process_date(df_main, '수납일')
if not df_comm.empty:
    df_comm = process_date(df_comm, '수납일')

# --- 사이드바 ---
st.sidebar.title("🏨 온리프 관리 시스템")
menu = st.sidebar.radio("메뉴 이동", ["🌐 전체 매출 요약", "💸 수수료 매출 분석"])
month_list = sorted(df_main['매출월'].unique(), reverse=True)
sel_month = st.sidebar.selectbox("📅 조회 월 선택", month_list)

# --- 메뉴 1: 전체 매출 ---
if menu == "🌐 전체 매출 요약":
    st.title("🌐 국적 및 권역별 매출 요약")
    m_df = df_main[df_main['매출월'] == sel_month]
    
    amt_col = [c for c in m_df.columns if '수납액' in c and 'CRM' in c]
    val_col = amt_col[0] if amt_col else m_df.columns[-1]
    m_df['매출_순수'] = m_df[val_col].apply(to_numeric) / 1.1
    
    total = m_df['매출_순수'].sum()
    st.metric(f"{sel_month} 총 매출액 (VAT 제외)", f"{total:,.0f}원")
    
    c1, c2 = st.columns(2)
    with c1:
        # 국적별 차트
        fig = px.pie(m_df, values='매출_순수', names='국적', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        # 상세 표 (우측 정렬)
        res_df = m_df.groupby('국적')['매출_순수'].sum().reset_index().sort_values('매출_순수', ascending=False)
        res_df['매출액'] = res_df['매출_순수'].apply(lambda x: f"{int(x):,}")
        st.dataframe(res_df[['국적', '매출액']], use_container_width=True, hide_index=True, 
                     column_config={"매출액": st.column_config.TextColumn(alignment="right")})

# --- 메뉴 2: 수수료 분석 ---
else:
    st.title("💸 수수료 및 유입 경로 분석")
    if not df_comm.empty:
        c_df = df_comm[df_comm['매출월'] == sel_month]
        
        # 컬럼 찾기
        fee_col = [c for c in c_df.columns if '수수료' in c or '정산금' in c]
        rev_col = [c for c in c_df.columns if '수납액' in c]
        
        if fee_col and rev_col:
            c_df['f_num'] = c_df[fee_col[0]].apply(to_numeric)
            c_df['r_num'] = c_df[rev_col[0]].apply(to_numeric)
            
            t_rev = c_df['r_num'].sum()
            t_fee = c_df['f_num'].sum()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("총 수납액", f"{t_rev:,.0f}원")
            m2.metric("총 수수료", f"{t_fee:,.0f}원")
            m3.metric("수수료 비중", f"{(t_fee/t_rev*100):.1f}%" if t_rev>0 else "0%")
            
            st.divider()
            
            # 경로별 비중
            path_col = [c for c in c_df.columns if '유입경로' in c]
            if path_col:
                p_df = c_df.groupby(path_col[0])['f_num'].sum().reset_index()
                fig_p = px.pie(p_df, values='f_num', names=path_col[0], title="경로별 수수료 비중", hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)
                
            st.subheader("📋 수수료 상세 리스트")
            c_df['수납액'] = c_df['r_num'].apply(lambda x: f"{int(x):,}")
            c_df['수수료'] = c_df['f_num'].apply(lambda x: f"{int(x):,}")
            show_cols = [c for c in ['수납일', '이름', path_col[0] if path_col else None, '수납액', '수수료'] if c]
            st.dataframe(c_df[show_cols], use_container_width=True, hide_index=True,
                         column_config={"수납액": st.column_config.TextColumn(alignment="right"), 
                                        "수수료": st.column_config.TextColumn(alignment="right")})
