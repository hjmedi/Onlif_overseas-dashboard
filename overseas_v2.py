import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 통합 데이터 센터", layout="wide")

# ⚠️ 여기에 '수납raw' 시트의 CSV 주소를 따옴표 안에 넣어주세요
CSV_URL = "https://docs.google.com/spreadsheets/d/1fZ0uLCwC4wqirxy_WFbfOwmbIeLpPRfsIBEwqC4hdIE/edit?gid=0#gid=0"
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
    
    # 데이터 정리
    df = raw_data.copy()
    headers = df.iloc[header_idx].fillna('미지정').astype(str).tolist()
    
    # 💡 중복된 컬럼 이름 해결 로직 (핵심!)
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

    st.title("📊 온리프 실시간 데이터 센터")
    
    # --- 화면 구성 ---
    # 국적 데이터가 있는 경우 (고객 분석)
    if '국적' in df.columns:
        st.subheader("👥 해외 고객 유입 분석")
        c1, c2 = st.columns(2)
        with c1:
            n_df = df['국적'].value_counts().reset_index()
            n_df.columns = ['국적', '방문자수']
            fig1 = px.pie(n_df, values='방문자수', names='국적', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            p_col = [c for c in df.columns if '유입경로' in c and '대분류' in c]
            if p_col:
                p_df = df[p_col[0]].value_counts().head(5).reset_index()
                p_df.columns = ['경로', '인원수']
                fig2 = px.bar(p_df, x='인원수', y='경로', orientation='h', color='경로')
                st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("📋 데이터 상세 리스트")
    # 전체 데이터 표 보여주기
    st.dataframe(df, use_container_width=True)

else:
    st.error("데이터 로딩 실패! 구글 시트 주소를 확인해주세요.")
