import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# 1. 페이지 기본 설정
st.set_page_config(page_title="온리프 해외 데이터 센터", layout="wide")

# ⚠️ 여기에 '수납raw' 시트의 CSV 주소를 다시 붙여넣으세요.
# (주소 끝이 반드시 output=csv 로 끝나야 합니다!)
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRsH0xOUdAP2Sp4rulPM1uejTOzCZFmoiBJ4z3rTlUvtihQebdh3Q1uMLGmuuCg7zR8uupz4kfLHBQ_/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=30)
def get_data(url):
    try:
        res = requests.get(url)
        if res.status_code == 200:
            df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')), header=None)
            return df
        else:
            return None
    except:
        return None

raw_data = get_data(CSV_URL)

if raw_data is not None:
    # --- 데이터 헤더 찾기 (이름, 국적 등 키워드로 행 탐색) ---
    header_idx = 0
    for i in range(len(raw_data)):
        row_content = raw_data.iloc[i].fillna('').astype(str).tolist()
        row_str = " ".join(row_content)
        if any(k in row_str for k in ['이름', '국적', '구분', '날짜']):
            header_idx = i
            break
    
    # 데이터 정리 및 중복 제목 해결
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

    # 🔥 [필터링 로직] T열(국내/해외 구분)에서 '해외'만 남기기
    # '국내/해외'라는 단어가 들어간 컬럼을 자동으로 찾습니다.
    target_col = [c for c in df.columns if '국내' in c or '해외' in c]
    
    if target_col:
        # 해당 열에 '해외'라는 글자가 포함된 행만 유지
        df = df[df[target_col[0]].str.contains('해외', na=False)]
    
    st.title("📊 온리프 해외 고객 실시간 분석")
    st.success(f"✅ 현재 해외 환자 데이터 **{len(df)}건**을 분석 중입니다.")

    # --- 시각화 ---
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🌐 국적별 비중")
            n_df = df['국적'].value_counts().reset_index()
            n_df.columns = ['국적', '방문자수']
            fig1 = px.pie(n_df, values='방문자수', names='국적', hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("🔍 주요 유입 경로")
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
        st.warning("데이터는 불러왔으나 '해외'로 분류된 데이터가 없습니다. 시트의 T열을 확인해주세요.")

else:
    st.error("🚨 데이터 로딩 실패! 구글 시트 주소가 'CSV' 형식인지, 혹은 주소가 정확한지 확인해주세요.")
