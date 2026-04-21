import streamlit as st
import pandas as pd
import requests
from io import StringIO
from datetime import timedelta

# 1. 페이지 설정
st.set_page_config(page_title="주간 회의 대시보드", layout="wide")

st.title("📊 주간 회의 실적 분석 (WoW / MoM)")
st.info("이 대시보드는 주간 회의용 스프레드시트 데이터를 기반으로 전주 및 전월 실적을 비교합니다.")

# 🔗 주간 회의용 구글 스프레드시트 전용 링크 (CSV 내보내기 형식)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1FQSWFSHKiSs6je8i9s9Dn_T_6rSgT649qz0t_WHatQk/export?format=csv&gid=974779251"

@st.cache_data(ttl=60)
def load_meeting_data():
    try:
        res = requests.get(SHEET_URL)
        res.raise_for_status()
        # 한글 깨짐 방지를 위해 utf-8-sig 사용
        df = pd.read_csv(StringIO(res.content.decode('utf-8-sig')))
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

df_raw = load_meeting_data()

if not df_raw.empty:
    # 사이드바 설정 영역
    st.sidebar.header("⚙️ 분석 설정")
    cols = df_raw.columns.tolist()
    
    # 사용자가 직접 날짜와 지표 컬럼을 선택 (시트마다 다를 수 있으므로)
    date_col = st.sidebar.selectbox("📅 날짜 컬럼 선택", cols)
    metric_col = st.sidebar.selectbox("💰 실적(숫자) 컬럼 선택", cols)
    
    if st.sidebar.button("실적 분석 실행"):
        df = df_raw.copy()
        
        # 데이터 정제
        df['날짜형'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['날짜형'])
        
        # 숫자형 변환 (콤마, 원화 기호 등 제거)
        df[metric_col] = pd.to_numeric(
            df[metric_col].astype(str).str.replace(',', '').str.replace('₩', '').str.replace(' ', ''), 
            errors='coerce'
        ).fillna(0)
        
        # 기준일 (데이터상 최신 날짜)
        max_date = df['날짜형'].max()
        
        # --- 🚀 주간(WoW) 계산 ---
        cw_start = max_date - timedelta(days=6) # 당주 (최신일 포함 7일)
        cw_val = df[(df['날짜형'] >= cw_start) & (df['날짜형'] <= max_date)][metric_col].sum()
        
        pw_end = cw_start - timedelta(days=1)
        pw_start = pw_end - timedelta(days=6) # 전주 (당주 이전 7일)
        pw_val = df[(df['날짜형'] >= pw_start) & (df['날짜형'] <= pw_end)][metric_col].sum()
        
        wow_rate = (cw_val - pw_val) / pw_val * 100 if pw_val > 0 else 0
        
        # --- 🚀 월간(MoM) 계산 ---
        cm_start = max_date.replace(day=1) # 당월 1일
        cm_val = df[(df['날짜형'] >= cm_start) & (df['날짜형'] <= max_date)][metric_col].sum()
        
        pm_end = cm_start - timedelta(days=1) # 전월 말일
        pm_start = pm_end.replace(day=1) # 전월 1일
        pm_val = df[(df['날짜형'] >= pm_start) & (df['날짜형'] <= pm_end)][metric_col].sum()
        
        mom_rate = (cm_val - pm_val) / pm_val * 100 if pm_val > 0 else 0
        
        # 결과 표시
        st.divider()
        st.subheader(f"💡 분석 기준일: {max_date.strftime('%Y-%m-%d')}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.metric(
                label=f"주간 실적 (WoW)", 
                value=f"{cw_val:,.0f}", 
                delta=f"{wow_rate:.1f}% (전주 대비)"
            )
            st.caption(f"당주: {cw_start.strftime('%m.%d')}~{max_date.strftime('%m.%d')} / 전주: {pw_start.strftime('%m.%d')}~{pw_end.strftime('%m.%d')}")
            
        with c2:
            st.metric(
                label=f"월간 실적 (MoM)", 
                value=f"{cm_val:,.0f}", 
                delta=f"{mom_rate:.1f}% (전월 대비)"
            )
            st.caption(f"당월: {cm_start.strftime('%m.%d')}~{max_date.strftime('%m.%d')} / 전월: {pm_start.strftime('%m.%d')}~{pm_end.strftime('%m.%d')}")

    # 원본 데이터 확인용 (참고용)
    with st.expander("📂 원본 데이터 확인"):
        st.write(df_raw)
else:
    st.warning("데이터를 불러오지 못했습니다. 구글 시트의 공유 설정(링크가 있는 모든 사용자에게 공개)을 확인해 주세요.")
