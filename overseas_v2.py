import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 매출 월별 분석", layout="wide")

# ✅ 수납raw 시트 CSV 주소
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except: return None

def to_numeric(val):
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 제목줄 찾기 ---
    header_idx = 0
    for i in range(len(raw_data)):
        row_str = " ".join(raw_data.iloc[i].fillna('').astype(str))
        if '이름' in row_str and '국적' in row_str:
            header_idx = i
            break
    
    df = raw_data.copy()
    df.columns = [str(c).strip() for c in df.iloc[header_idx].fillna('미지정')]
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)

    # 1️⃣ [필터] 해외 데이터만 추출
    filter_col = [c for c in df.columns if '국내' in c or '해외' in c or '구분' in c]
    if filter_col:
        df = df[df[filter_col[0]].astype(str).str.contains('해외', na=False)]

    # 2️⃣ [매출액 계산] '수납액 (CRM)' 컬럼 처리
    amt_col = [c for c in df.columns if '수납액' in c and 'CRM' in c]
    if not amt_col:
        amt_col = [c for c in df.columns if '수납액' in c or '금액' in c]
    
    if amt_col:
        df['매출액_숫자'] = df[amt_col[0]].apply(to_numeric)
    else:
        df['매출액_숫자'] = 0

    # 3️⃣ [날짜 처리] E열 '수납일'을 월 단위로 변환
    date_col = [c for c in df.columns if '수납일' in c]
    if date_col:
        df['날짜형식'] = pd.to_datetime(df[date_col[0]], errors='coerce')
        df['매출월'] = df['날짜형식'].dt.strftime('%Y년 %m월')
    else:
        df['매출월'] = "날짜미상"

    # ------------------ 사이드바 설정 ------------------
    st.sidebar.header("📊 메뉴 이동")
    st.sidebar.radio("원하시는 리스트를 선택하세요:", ["🌐 전체 매출 요약 (원형 그래프)"])
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 조회할 월을 선택하세요")
    
    # 데이터에 있는 월 목록 추출 (정렬됨)
    month_list = sorted(df['매출월'].dropna().unique(), reverse=True)
    selected_month = st.sidebar.selectbox("월 선택", month_list)

    # 선택된 월로 데이터 필터링
    filtered_df = df[df['매출월'] == selected_month]
    # --------------------------------------------------

    st.title(f"📊 온리프 해외매출 국적별 비중 분석")
    st.caption(f"📍 {selected_month} 해외매출 종합")
    
    # 상단 요약 지표 (선택된 월 기준)
    month_revenue = filtered_df['매출액_숫자'].sum()
    st.header(f"{month_revenue:,.0f}원")
    st.divider()

    if not filtered_df.empty:
        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.subheader("🌐 국적별 매출 비중")
            n_df = filtered_df.groupby('국적')['매출액_숫자'].sum().reset_index()
            fig1 = px.pie(n_df, values='매출액_숫자', names='국적', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig1.update_traces(textinfo='percent+label', texttemplate='%{label}<br>%{percent}')
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.subheader(f"📊 {selected_month} 국적별 상세 실적")
            # 표 형태의 데이터 정리
            table_df = n_df.sort_values(by='매출액_숫자', ascending=False).reset_index(drop=True)
            table_df['비중'] = (table_df['매출액_숫자'] / month_revenue * 100).map('{:.1f}%'.format)
            table_df['매출액'] = table_df['매출액_숫자'].map('{:,.0f}'.format)
            st.table(table_df[['국적', '매출액', '비중']])
        
        st.divider()
        st.subheader(f"🔍 {selected_month} 주요 유입 경로")
        p_col = [c for c in df.columns if '유입경로' in c]
        if p_col:
            p_df = filtered_df.groupby(p_col[0])['매출액_숫자'].sum().sort_values(ascending=True).reset_index()
            p_
