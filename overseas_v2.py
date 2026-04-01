import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 고객 분석", layout="wide")

# ⚠️ 여기에 '수납raw' 시트의 CSV 주소를 다시 붙여넣으세요.
CSV_URL = "여기에_주소를_넣으세요"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        # CSV 읽기 (헤더가 2번째 줄쯤 있을 것을 대비해 유연하게 로드)
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except:
        return None

raw_df = get_data(CSV_URL)

if raw_df is not None:
    # 데이터 정리: 보통 2행(index 1)이 제목인 경우가 많음
    df = raw_df.copy()
    df.columns = df.iloc[1] # 2번째 줄을 제목으로 설정
    df = df.drop([0, 1]).reset_index(drop=True) # 위쪽 빈 줄 삭제

    st.title("👥 해외 고객 유입 분석 리포트")
    st.info("💡 '수납raw' 시트의 데이터를 실시간으로 분석 중입니다.")

    # 사이드바 필터 (국적 선택 등)
    if '국적' in df.columns:
        nations = df['국적'].dropna().unique()
        selected_nation = st.sidebar.multiselect("분석할 국적 선택", nations, default=nations)
        df = df[df['국적'].isin(selected_nation)]

    # --- 대시보드 화면 구성 ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📍 국적별 유입 비중")
        if '국적' in df.columns:
            nation_counts = df['국적'].value_counts().reset_index()
            nation_counts.columns = ['국적', '인원수']
            fig_pie = px.pie(nation_counts, values='인원수', names='국적', hole=0.3,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("🚀 주요 유입 경로 (Top 5)")
        path_col = '최초 유입경로\n(대분류)' # 시트 제목에 맞춤
        if path_col in df.columns:
            path_counts = df[path_col].value_counts().head(5).reset_index()
            path_counts.columns = ['경로', '인원수']
            fig_bar = px.bar(path_counts, x='인원수', y='경로', orientation='h', color='경로')
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    
    # 상세 데이터 표
    st.subheader("📋 상세 고객 리스트")
    # 보여주고 싶은 컬럼만 선택 (시트에 있는 이름대로)
    cols_to_show = [c for c in ['고객등록일', '이름', '국적', '성별', '최초 유입경로\n(상세소분류)'] if c in df.columns]
    st.dataframe(df[cols_to_show], use_container_width=True)

else:
    st.error("데이터를 불러올 수 없습니다. 구글 시트 주소를 확인해주세요!")
