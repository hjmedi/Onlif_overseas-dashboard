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
        # 날짜 형식으로 변환 (에러나는 데이터는 무시)
        df['날짜형식'] = pd.to_datetime(df[date_col[0]], errors='coerce')
        # '연도-월' 형식의 문자열 생성
        df['매출월'] = df['날짜형식'].dt.strftime('%Y-%m')
    else:
        df['매출월'] = "날짜미상"

    st.title("📅 온리프 해외 매출 월별 분석 리포트")
    
    # 상단 요약 지표
    total_rev = df['매출액_숫자'].sum()
    st.metric(label="총 해외 매출 합계", value=f"{total_rev:,.0f} 원")
    st.divider()

    if not df.empty:
        # --- 월별 매출 추이 그래프 (추가됨) ---
        st.subheader("📈 월별 매출 추이")
        monthly_df = df.dropna(subset=['매출월']).groupby('매출월')['매출액_숫자'].sum().reset_index()
        monthly_df = monthly_df.sort_values('매출월') # 시간순 정렬
        
        fig_line = px.line(monthly_df, x='매출월', y='매출액_숫자', text=monthly_df['매출액_숫자'].apply(lambda x: f"{x:,.0f}"),
                          title="월별 매출 흐름", markers=True)
        fig_line.update_traces(textposition="top center")
        st.plotly_chart(fig_line, use_container_width=True)

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌐 국적별 매출 비중")
            n_df = df.groupby('국적')['매출액_숫자'].sum().reset_index()
            fig1 = px.pie(n_df, values='매출액_숫자', names='국적', hole=0.4)
            fig1.update_traces(textinfo='percent+value', texttemplate='%{label}<br>%{value:,.0f}원')
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.subheader("🔍 유입 경로별 매출")
            p_col = [c for c in df.columns if '유입경로' in c]
            if p_col:
                p_df = df.groupby(p_col[0])['매출액_숫자'].sum().sort_values(ascending=True).reset_index()
                p_df.columns = ['경로', '매출액']
                fig2 = px.bar(p_df, x='매출액', y='경로', orientation='h', text_auto=',.0f', color='경로')
                st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        st.subheader("📋 상세 내역 (검증용)")
        show_cols = [c for c in ['수납일', '매출월', '이름', '국적', amt_col[0] if amt_col else None] if c in df.columns or c == '매출월']
        st.dataframe(df[show_cols], use_container_width=True)
    else:
        st.warning("데이터가 없습니다.")
else:
    st.error("데이터 로딩 실패")
