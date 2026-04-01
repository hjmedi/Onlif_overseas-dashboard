import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 고객 분석", layout="wide")

# ⚠️ 여기에 '수납raw' 시트의 CSV 주소를 따옴표 안에 넣어주세요
CSV_URL = "https://docs.google.com/spreadsheets/d/1fZ0uLCwC4wqirxy_WFbfOwmbIeLpPRfsIBEwqC4hdIE/edit?gid=0#gid=0"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        # 한글 깨짐 방지를 위해 utf-8-sig 사용
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
        return df
    except:
        return None

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 데이터 자동 찾기 로직 ---
    # 시트 전체에서 '이름'이나 '국적'이라는 글자가 들어있는 행을 제목줄로 인식합니다.
    header_idx = 0
    for i in range(len(raw_data)):
        row_str = "".join(raw_data.iloc[i].astype(str))
        if '이름' in row_str or '국적' in row_str:
            header_idx = i
            break
    
    # 제목 설정 및 위쪽 빈 행 삭제
    df = raw_data.copy()
    df.columns = df.iloc[header_idx]
    df = df.drop(range(header_idx + 1)).reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns] # 제목 양옆 공백 제거

    st.title("👥 해외 고객 유입 실시간 분석")
    st.info("📍 '수납raw' 시트 데이터를 기반으로 리포트를 생성합니다.")

    # 데이터가 비어있지 않은지 확인
    if not df.empty and '국적' in df.columns:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🌐 국적별 방문 비중")
            # 국적별 카운트 (데이터가 있는 것만)
            nation_df = df['국적'].value_counts().reset_index()
            nation_df.columns = ['국적', '방문자수']
            fig_pie = px.pie(nation_counts, values='방문자수', names='국적', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader("🔍 주요 유입 경로")
            # 유입경로 컬럼 찾기 (이름이 조금씩 달라도 찾을 수 있게)
            path_col = [c for c in df.columns if '유입경로' in c and '대분류' in c]
            if path_col:
                path_counts = df[path_col[0]].value_counts().head(10).reset_index()
                path_counts.columns = ['경로', '인원수']
                fig_bar = px.bar(path_counts, x='인원수', y='경로', orientation='h', color='경로')
                st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.subheader("📝 상세 리스트")
        # 주요 컬럼만 골라서 표로 보여주기
        target_cols = ['고객등록일', '이름', '국적', '성별']
        valid_cols = [c for c in target_cols if c in df.columns]
        st.dataframe(df[valid_cols], use_container_width=True)
    else:
        st.warning("시트에서 '국적' 또는 '이름' 컬럼을 찾을 수 없습니다. 시트의 제목줄을 확인해 주세요.")

else:
    st.error("구글 시트 링크가 올바르지 않거나 데이터를 읽을 수 없습니다.")
