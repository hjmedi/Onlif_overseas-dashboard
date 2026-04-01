import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 데이터 센터", layout="wide")

# ⚠️ 여기에 '수납raw' 시트의 CSV 주소를 따옴표 안에 넣어주세요
CSV_URL = "여기에_주소를_넣으세요"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except:
        return None

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 데이터 헤더 찾기 ---
    header_idx = 0
    for i in range(len(raw_data)):
        row_content = raw_data.iloc[i].fillna('').astype(str).tolist()
        row_str = " ".join(row_content)
        if any(k in row_str for k in ['이름', '국적', '권역', '날짜']):
            header_idx = i
            break
    
    # 데이터 정리 및 중복 컬럼 해결
    df = raw_data.copy()
    headers = df.iloc[header_idx].fillna('미지정').astype(str).tolist()
    
    new_headers = []
    counts = {}
    for h in headers:
        h = h.strip()
        if h in counts:
            counts[h] += 1
            new_headers.append(f"{h}_{counts[h]}")
        else:
            counts[h] = 0
            new_headers.append(h)
    
    df.columns = new_headers
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)

    # 🔥 [추가된 부분] T열(국내/해외매출 구분)에서 '해외' 데이터만 추출
    # 시트의 T열 제목이 '국내/해외매출 구분'이라고 가정합니다.
    filter_col = '국내/해외매출 구분' 
    if filter_col in df.columns:
        # '해외' 글자가 포함된 데이터만 필터링 (국내 제외)
        df = df[df[filter_col].str.contains('해외', na=False)]
    
    st.title("📊 온리프 해외 고객 분석 (해외매출 전용)")
    st.info(f"💡 현재 국내 매출을 제외한 **'{len(df)}건'**의 해외 환자 데이터를 분석 중입니다.")
    
    # --- 화면 구성 ---
    if '국적' in df.columns:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌐 해외 국적별 비중")
            n_df = df['국적'].value_counts().reset_index()
            n_df.columns = ['국적', '방문자수']
            fig1 = px.pie(n_df, values='방문자수', names='국적', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("🔍 해외 유입 경로")
            p_col = [c for c in df.columns if '유입경로' in c and '대분류' in c]
            if p_col:
                p_df = df[p_col[0]].value_counts().head(5).reset_index()
                p_df.columns = ['경로', '인원수']
                fig2 = px.bar(p_df, x='인원수', y='경로', orientation='h', color='경로')
                st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📋 상세 해외 고객 리스트")
    st.dataframe(df, use_container_width=True)

else:
    st.error("데이터 로딩 실패!")
