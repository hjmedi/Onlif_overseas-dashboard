import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 데이터 센터", layout="wide")

# ⚠️ 구글 시트 '수납raw' 시트의 CSV 주소를 따옴표 안에 넣어주세요
CSV_URL = "https://docs.google.com/spreadsheets/d/1fZ0uLCwC4wqirxy_WFbfOwmbIeLpPRfsIBEwqC4hdIE/edit?gid=0#gid=0"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        # 한글 깨짐 방지 및 데이터 로드
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except:
        return None

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 데이터 헤더 자동 탐색 (강화 버전) ---
    header_idx = 0
    # 전체 행을 돌며 '이름', '국적', '권역' 중 하나라도 포함된 행을 찾습니다.
    for i in range(len(raw_data)):
        row_content = raw_data.iloc[i].fillna('').astype(str).tolist()
        row_str = " ".join(row_content)
        if any(keyword in row_str for keyword in ['이름', '국적', '권역', '날짜']):
            header_idx = i
            break
    
    # 데이터 정리
    df = raw_data.copy()
    df.columns = df.iloc[header_idx]
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns] # 제목 공백 제거

    st.title("📊 온리프 실시간 데이터 분석")
    st.caption("📍 구글 스프레드시트와 실시간 연동 중")

    # --- 1. 만약 '수납raw' 데이터라면 (고객 분석) ---
    if '국적' in df.columns:
        st.subheader("👥 해외 고객 유입 분석")
        col1, col2 = st.columns(2)
        with col1:
            # 국적별 비중
            nation_df = df['국적'].value_counts().reset_index()
            nation_df.columns = ['국적', '방문자수']
            fig_pie = px.pie(nation_df, values='방문자수', names='국적', hole=0.4, title="국적별 비중")
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            # 유입 경로 분석 (대분류 컬럼 자동 탐색)
            path_col = [c for c in df.columns if '유입경로' in c and '대분류' in c]
            if path_col:
                path_df = df[path_col[0]].value_counts().head(5).reset_index()
                path_df.columns = ['경로', '인원수']
                fig_bar = px.bar(path_df, x='인원수', y='경로', orientation='h', color='경로', title="주요 유입 경로")
                st.plotly_chart(fig_bar, use_container_width=True)

    # --- 2. 만약 매출 데이터라면 (기존 매출 분석) ---
    elif '권역' in df.columns:
        st.subheader("💰 권역별 매출 현황")
        # 매출 관련 로직을 여기에 추가할 수 있습니다.
        st.write("매출 시트 데이터가 감지되었습니다.")

    st.divider()
    st.subheader("📋 데이터 상세 리스트")
    st.dataframe(df, use_container_width=True)

else:
    st.error("데이터를 불러오지 못했습니다. 구글 시트 주소가 'CSV 형식'인지 확인해 주세요.")
