import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 매출 검증 대시보드", layout="wide")

# ✅ 보내주신 수납raw 시트의 CSV 주소입니다.
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        # 한글 깨짐 방지 및 데이터 로드
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except:
        return None

def to_numeric(val):
    """금액 문자열(₩1,234)을 숫자(1234)로 변환"""
    if pd.isna(val): return 0
    s = str(val).replace('₩', '').replace(',', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 데이터 헤더 탐색 (이름, 국적, 금액 등 키워드 기준) ---
    header_idx = 0
    for i in range(len(raw_data)):
        row_str = " ".join(raw_data.iloc[i].fillna('').astype(str))
        if any(k in row_str for k in ['이름', '국적', '금액', '구분']):
            header_idx = i
            break
    
    # 데이터 정리
    df = raw_data.copy()
    headers = [str(h).strip() for h in df.iloc[header_idx].fillna('미지정')]
    
    # 중복된 컬럼 이름 해결 (에러 방지)
    new_headers = []
    counts = {}
    for h in headers:
        if h in counts:
            counts[h] += 1
            new_headers.append(f"{h}_{counts[h]}")
        else:
            counts[h] = 0
            new_headers.append(h)
    df.columns = new_headers
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)

    # 🔥 [필터링] T열(국내/해외매출 구분)에서 '해외'만 추출
    target_col = [c for c in df.columns if '국내' in c or '해외' in c]
    if target_col:
        df = df[df[target_col[0]].str.contains('해외', na=False)]

    # 🔥 [금액 계산] 매출액 컬럼(수납금액 등) 자동 탐색 및 숫자 변환
    amt_col = [c for c in df.columns if '수납금액' in c or '결제금액' in c or '금액' in c]
    if amt_col:
        df['매출액_숫자'] = df[amt_col[0]].apply(to_numeric)
    else:
        df['매출액_숫자'] = 0

    st.title("💰 온리프 해외 매출 검증 리포트")
    
    # --- 상단 요약 지표 ---
    total_revenue = df['매출액_숫자'].sum()
    st.metric(label="총 해외 매출 합계 (필터 적용 후)", value=f"{total_revenue:,.0f} 원")
    st.info(f"💡 현재 시트에서 **{len(df)}건**의 해외 환자 데이터를 분석하고 있습니다.")
    st.divider()

    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌐 국적별 매출 비중 (금액 포함)")
            # 국적별 매출 합계 계산
            n_df = df.groupby('국적')['매출액_숫자'].sum().reset_index()
            fig1 = px.pie(n_df, values='매출액_숫자', names='국적', hole=0.4)
            # 그래프 안에 %와 실제 금액을 함께 표시
            fig1.update_traces(textinfo='percent+value', texttemplate='%{label}<br>%{percent}<br>%{value:,.0f}원')
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.subheader("🔍 주요 유입 경로별 매출")
            p_cols = [c for c in df.columns if '유입경로' in c and '대분류' in c]
            if p_cols:
                p_df = df.groupby(p_cols[0])['매출액_숫자'].sum().sort_values(ascending=True).reset_index()
                p_df.columns = ['경로', '매출액']
                fig2 = px.bar(p_df, x='매출액', y='경로', orientation='h', 
                             text_auto=',.0f', color='경로')
                st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        st.subheader("📋 상세 내역 (데이터 검증용)")
        # 검증에 필요한 핵심 컬럼들만 표시
        valid_cols = [c for c in ['고객등록일', '이름', '국적', target_col[0] if target_col else None, amt_col[0] if amt_col else None] if c]
        st.dataframe(df[valid_cols], use_container_width=True)
    else:
        st.warning("분석할 해외 데이터가 없습니다. 시트의 구분을 확인해 주세요.")

else:
    st.error("🚨 데이터 로딩 실패! 시트 주소가 정확한지 확인해 주세요.")
